"""Waxpeer.com scraper - uses official API (docs.waxpeer.com).

Requires API key. Set WAXPEER_API_KEY env var.
Get your key from waxpeer.com account settings.
"""

import logging

from app.config import settings
from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class WaxpeerScraper(BaseScraper):
    marketplace_slug = "waxpeer"
    marketplace_name = "Waxpeer"
    scraper_type = "api"

    # GET /v1/prices — returns {name: price} for all items
    API_URL = "https://api.waxpeer.com/v1/prices"

    async def scrape(self) -> list[ScrapedItem]:
        items = []

        api_key = getattr(settings, "WAXPEER_API_KEY", "")
        params = {"game": "csgo", "min_price": 100, "max_price": 1000000}
        if api_key:
            params["api"] = api_key
        else:
            logger.warning("Waxpeer: no API key configured (WAXPEER_API_KEY) — requests may fail")

        data = await fetch_json(self.API_URL, params=params)
        if not data or not data.get("success"):
            logger.warning("Waxpeer: no data from /v1/prices")
            return items

        results = data.get("items", data.get("data", []))
        if isinstance(results, dict):
            # Format: {name: price} or {name: {price: N, ...}}
            for name, price_info in results.items():
                price = price_info if isinstance(price_info, (int, float)) else price_info.get("price", 0)
                # Waxpeer prices are in thousandths of a dollar (1000 = $1)
                if isinstance(price, (int, float)) and price > 10000:
                    price = price / 1000
                if price <= 0:
                    continue
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    item_type=classify_item_type(name),
                ))
        else:
            for item in results:
                name = item.get("name", "")
                price = item.get("min", item.get("price", 0))
                if isinstance(price, (int, float)) and price > 10000:
                    price = price / 1000
                if not name or price <= 0:
                    continue
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    icon_url=item.get("img") or item.get("icon_url"),
                    item_type=classify_item_type(name),
                ))

        logger.info(f"Waxpeer: scraped {len(items)} items")
        return items
