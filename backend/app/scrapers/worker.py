"""Scraper worker — runs periodic scrape cycles."""

import asyncio
import logging
import sys

from app.config import settings
from app.scrapers.scheduler import run_full_scrape_cycle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("scraper.worker")


async def worker_loop():
    """Main worker loop — runs scrape cycles at configured intervals."""
    interval = settings.SCRAPE_INTERVAL_MINUTES * 60
    logger.info(f"Scraper worker started. Interval: {settings.SCRAPE_INTERVAL_MINUTES} minutes")

    # Wait for services to be ready
    await asyncio.sleep(5)

    while True:
        try:
            await run_full_scrape_cycle()
        except Exception as e:
            logger.error(f"Scrape cycle failed: {e}", exc_info=True)

        logger.info(f"Next scrape in {settings.SCRAPE_INTERVAL_MINUTES} minutes...")
        await asyncio.sleep(interval)


def main():
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
