"""Scheduler for periodic scraping tasks."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.config import settings
from app.db.session import async_session_maker
from app.models.marketplace import Marketplace
from app.scrapers.registry import get_scraper
from app.services.arbitrage_service import calculate_arbitrage_for_item
from app.services.price_service import get_latest_steam_price
from app.models.price import PriceSnapshot

logger = logging.getLogger(__name__)


async def run_scraper_for_marketplace(marketplace: Marketplace) -> dict:
    """Run a single marketplace scraper and trigger arbitrage calculation."""
    scraper = get_scraper(marketplace.slug)
    if not scraper:
        logger.warning(f"No scraper registered for {marketplace.slug}")
        return {"status": "skipped", "reason": "no scraper"}

    result = await scraper.run(marketplace.id)

    # Update last_scraped_at
    async with async_session_maker() as db:
        mkt = (await db.execute(
            select(Marketplace).where(Marketplace.id == marketplace.id)
        )).scalar_one_or_none()
        if mkt:
            mkt.last_scraped_at = datetime.now(timezone.utc)
            await db.commit()

    return result


async def run_arbitrage_calculation():
    """Recalculate arbitrage opportunities for all items with fresh prices."""
    logger.info("Starting arbitrage recalculation...")
    async with async_session_maker() as db:
        # Get all unique item_ids that have prices
        from sqlalchemy import distinct
        item_ids_result = await db.execute(
            select(distinct(PriceSnapshot.item_id))
        )
        item_ids = [row[0] for row in item_ids_result.all()]

        calculated = 0
        for item_id in item_ids:
            steam_price = await get_latest_steam_price(db, item_id)
            if steam_price and steam_price > 0:
                await calculate_arbitrage_for_item(db, item_id, steam_price)
                calculated += 1

        await db.commit()
        logger.info(f"Arbitrage recalculated for {calculated} items")


async def run_full_scrape_cycle():
    """Run a complete scrape cycle: all enabled marketplaces then arbitrage."""
    logger.info("=== Starting full scrape cycle ===")

    async with async_session_maker() as db:
        result = await db.execute(
            select(Marketplace).where(Marketplace.is_enabled.is_(True))
        )
        marketplaces = list(result.scalars().all())

    # Always scrape Steam first
    steam_mkts = [m for m in marketplaces if m.slug == "steam"]
    other_mkts = [m for m in marketplaces if m.slug != "steam"]

    # Scrape Steam prices first
    for mkt in steam_mkts:
        logger.info(f"Scraping {mkt.name}...")
        await run_scraper_for_marketplace(mkt)

    # Scrape other marketplaces concurrently (with concurrency limit)
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_SCRAPERS)

    async def _scrape_with_limit(mkt):
        async with semaphore:
            logger.info(f"Scraping {mkt.name}...")
            return await run_scraper_for_marketplace(mkt)

    tasks = [_scrape_with_limit(mkt) for mkt in other_mkts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for mkt, res in zip(other_mkts, results):
        if isinstance(res, Exception):
            logger.error(f"Scraper for {mkt.name} failed: {res}")
        else:
            logger.info(f"Scraper for {mkt.name}: {res}")

    # Calculate arbitrage opportunities
    await run_arbitrage_calculation()

    logger.info("=== Full scrape cycle complete ===")
