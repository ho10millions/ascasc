"""White.Market scraper - uses S3 price export JSON (no auth required)."""

import logging

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class WhiteMarketScraper(BaseScraper):
    marketplace_slug = "white-market"
    marketplace_name = "White Market"
    scraper_type = "api"

    # Public price export — no API key needed, updated frequently
    PRICES_URL = "https://s3.white.market/export/v1/prices/730.json"

    async def scrape(self) -> list[ScrapedItem]:
        items = []

        data = await fetch_json(self.PRICES_URL)
        if not data:
            logger.warning("White Market: no data from S3 price export")
            return items

        # The export returns a list of items or a dict with items
        results = data if isinstance(data, list) else data.get("items", data.get("data", []))

        for item in results:
            try:
                name = item.get("market_hash_name") or item.get("marketHashName") or item.get("name", "")
                # Price may be in different fields
                price = (
                    item.get("price")
                    or item.get("min_price")
                    or item.get("cheapest")
                    or item.get("lowest_price")
                    or 0
                )
                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        continue

                if not name or price <= 0:
                    continue

                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    icon_url=item.get("image") or item.get("icon_url"),
                    item_type=classify_item_type(name),
                    listing_count=item.get("count") or item.get("quantity"),
                ))
            except Exception as e:
                logger.debug(f"White Market: error parsing item: {e}")
                continue

        logger.info(f"White Market: scraped {len(items)} items from S3 export")
        return items
