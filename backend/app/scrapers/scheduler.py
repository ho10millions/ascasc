"""Scheduler — parallel HTTP fetch, sequential DB writes for SQLite safety."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, distinct

from app.db.session import async_session_maker
from app.models.marketplace import Marketplace
from app.models.price import PriceSnapshot
from app.models.scrape_job import ScrapeJob
from app.scrapers.registry import get_scraper
from app.services.arbitrage_service import calculate_arbitrage_for_item

logger = logging.getLogger(__name__)


async def fetch_marketplace_data(marketplace):
    """Phase 1: HTTP fetch only — no DB writes. Safe to run in parallel."""
    scraper = get_scraper(marketplace.slug)
    if not scraper:
        return marketplace, [], "no scraper"
    try:
        logger.info(f"[FETCH] {marketplace.name}...")
        items = await scraper.scrape()
        logger.info(f"[FETCH] {marketplace.name}: got {len(items)} items")
        return marketplace, items, None
    except Exception as e:
        logger.error(f"[FETCH] {marketplace.name} failed: {e}")
        return marketplace, [], str(e)


async def save_marketplace_results(marketplace, items, on_progress=None):
    """Phase 2: Save fetched items to DB. Must run sequentially for SQLite."""
    scraper = get_scraper(marketplace.slug)
    if not scraper or not items:
        return 0

    async with async_session_maker() as db:
        job = ScrapeJob(
            id=str(uuid.uuid4()),
            marketplace_id=marketplace.id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        db.add(job)
        await db.commit()

        try:
            saved_count = await scraper.save_results(db, items, marketplace.id)
            job.status = "completed"
            job.items_scraped = saved_count
            job.finished_at = datetime.now(timezone.utc)

            mkt = (await db.execute(
                select(Marketplace).where(Marketplace.id == marketplace.id)
            )).scalar_one_or_none()
            if mkt:
                mkt.last_scraped_at = datetime.now(timezone.utc)

            await db.commit()
            logger.info(f"[SAVE] {marketplace.name}: {saved_count} items saved")

            if on_progress:
                await on_progress(marketplace.slug, saved_count)
            return saved_count
        except Exception as e:
            job.status = "failed"
            job.errors = str(e)[:500]
            job.finished_at = datetime.now(timezone.utc)
            await db.commit()
            logger.error(f"[SAVE] {marketplace.name} failed: {e}")
            return 0


async def run_arbitrage_calculation(on_progress=None):
    """Recalculate arbitrage opportunities for all items with fresh prices."""
    logger.info("Starting arbitrage recalculation...")
    async with async_session_maker() as db:
        item_ids_result = await db.execute(
            select(distinct(PriceSnapshot.item_id))
        )
        item_ids = [row[0] for row in item_ids_result.all()]

        calculated = 0
        for item_id in item_ids:
            await calculate_arbitrage_for_item(db, item_id)
            calculated += 1

        await db.commit()
        logger.info(f"Arbitrage recalculated for {calculated} items")

    if on_progress:
        await on_progress("arbitrage_done", calculated)


async def run_full_scrape_cycle(on_progress=None):
    """Run a complete scrape cycle: parallel HTTP fetch + sequential DB saves."""
    logger.info("=== Starting full scrape cycle ===")

    async with async_session_maker() as db:
        result = await db.execute(
            select(Marketplace).where(Marketplace.is_enabled.is_(True))
        )
        marketplaces = list(result.scalars().all())

    steam_mkts = [m for m in marketplaces if m.slug == "steam"]
    other_mkts = [m for m in marketplaces if m.slug != "steam"]
    total_items = 0

    # --- Steam first (need baseline prices before arbitrage) ---
    for mkt in steam_mkts:
        mkt_ref, items, error = await fetch_marketplace_data(mkt)
        if items:
            saved = await save_marketplace_results(mkt_ref, items, on_progress)
            total_items += saved

    # --- Phase 1: Fetch ALL other marketplaces in PARALLEL (HTTP only) ---
    logger.info(f"Fetching {len(other_mkts)} marketplaces in parallel...")
    fetch_tasks = [fetch_marketplace_data(mkt) for mkt in other_mkts]
    fetch_results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    # --- Phase 2: Save results SEQUENTIALLY (SQLite-safe) ---
    for res in fetch_results:
        if isinstance(res, Exception):
            logger.error(f"Fetch task failed: {res}")
            continue
        mkt_ref, items, error = res
        if error:
            logger.warning(f"Skipping {mkt_ref.name}: {error}")
            continue
        if items:
            saved = await save_marketplace_results(mkt_ref, items, on_progress)
            total_items += saved

    # --- Phase 3: Calculate arbitrage ---
    await run_arbitrage_calculation(on_progress)

    logger.info(f"=== Full scrape cycle complete: {total_items} total items ===")
    return total_items
