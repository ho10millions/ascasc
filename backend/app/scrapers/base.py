import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_maker
from app.models.scrape_job import ScrapeJob
from app.services.item_service import get_or_create_item
from app.services.price_service import save_price_snapshot

logger = logging.getLogger(__name__)


@dataclass
class ScrapedItem:
    market_hash_name: str
    price_usd: float
    game: str = "cs2"
    icon_url: str | None = None
    item_type: str | None = None
    rarity: str | None = None
    listing_count: int | None = None


class BaseScraper(ABC):
    marketplace_slug: str
    marketplace_name: str
    scraper_type: str = "api"

    def __init__(self):
        self.logger = logging.getLogger(f"scraper.{self.marketplace_slug}")

    @abstractmethod
    async def scrape(self) -> list[ScrapedItem]:
        pass

    async def save_results(self, db: AsyncSession, items: list[ScrapedItem], marketplace_id: int) -> int:
        saved = 0
        for scraped in items:
            try:
                item = await get_or_create_item(
                    db,
                    game=scraped.game,
                    market_hash_name=scraped.market_hash_name,
                    icon_url=scraped.icon_url,
                    item_type=scraped.item_type,
                    rarity=scraped.rarity,
                )
                await save_price_snapshot(
                    db,
                    item_id=item.id,
                    marketplace_id=marketplace_id,
                    price_usd=scraped.price_usd,
                    listing_count=scraped.listing_count,
                )
                saved += 1
            except Exception as e:
                self.logger.error(f"Error saving item {scraped.market_hash_name}: {e}")
        return saved

    async def run(self, marketplace_id: int) -> dict:
        job_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        async with async_session_maker() as db:
            job = ScrapeJob(
                id=job_id,
                marketplace_id=marketplace_id,
                status="running",
                started_at=started_at,
            )
            db.add(job)
            await db.commit()

            try:
                self.logger.info(f"Starting scrape for {self.marketplace_name}")
                items = await self.scrape()
                self.logger.info(f"Scraped {len(items)} items from {self.marketplace_name}")

                saved_count = await self.save_results(db, items, marketplace_id)

                job.status = "completed"
                job.items_scraped = saved_count
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()

                self.logger.info(
                    f"Completed scrape for {self.marketplace_name}: {saved_count} items saved"
                )
                return {"status": "completed", "items_scraped": saved_count}

            except Exception as e:
                self.logger.error(f"Scrape failed for {self.marketplace_name}: {e}")
                job.status = "failed"
                job.errors = str(e)
                job.finished_at = datetime.now(timezone.utc)
                await db.commit()
                return {"status": "failed", "error": str(e)}
