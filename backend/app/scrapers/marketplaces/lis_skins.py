"""Lis-Skins.com scraper - uses official Public User API (/v1/market/search)."""

import logging

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class LisSkinsScraper(BaseScraper):
    marketplace_slug = "lis-skins"
    marketplace_name = "Lis-Skins"
    scraper_type = "api"

    # Official API documented at lis-skins-ru.stoplight.io
    API_URL = "https://api.lis-skins.ru/v1/market/search"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        page = 1
        while page <= 50:
            data = await fetch_json(
                self.API_URL,
                params={"page": page, "limit": 100, "app_id": 730},
            )
            if not data:
                break

            results = data.get("data", data.get("items", []))
            if not results:
                break

            for item in results:
                name = item.get("market_hash_name") or item.get("name", "")
                price = item.get("price", 0)
                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        continue
                # Convert cents to dollars if price seems too large
                if isinstance(price, (int, float)) and price > 10000:
                    price = price / 100

                if not name or price <= 0:
                    continue

                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    icon_url=item.get("image") or item.get("icon_url"),
                    item_type=classify_item_type(name),
                ))

            page += 1

        logger.info(f"Lis-Skins: scraped {len(items)} items")
        return items
