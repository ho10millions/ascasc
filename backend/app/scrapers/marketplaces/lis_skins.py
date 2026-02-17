"""Lis-Skins.com scraper - uses official Public User API (/v1/market/search).

Prices are returned as floats in USD (e.g. 12.50 = $12.50).
Docs: https://lis-skins-ru.stoplight.io/docs/lis-skins-ru-public-user-api
"""

import asyncio
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
        seen_names: dict[str, float] = {}
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
                try:
                    name = item.get("market_hash_name") or item.get("name", "")
                    price = item.get("price", 0)
                    if isinstance(price, str):
                        try:
                            price = float(price)
                        except ValueError:
                            continue

                    if not isinstance(price, (int, float)) or not name or price <= 0:
                        continue

                    price = float(price)

                    # Deduplicate — keep cheapest price per item name
                    if name in seen_names:
                        if price < seen_names[name]:
                            seen_names[name] = price
                        continue

                    seen_names[name] = price
                    items.append(ScrapedItem(
                        market_hash_name=name,
                        price_usd=round(price, 2),
                        game="cs2",
                        icon_url=item.get("image") or item.get("icon_url"),
                        item_type=classify_item_type(name),
                    ))
                except Exception as e:
                    logger.debug(f"Lis-Skins: error parsing item: {e}")
                    continue

            page += 1
            # Rate limit: small delay between pages
            await asyncio.sleep(0.5)

        # Update prices for deduplicated items
        for item in items:
            if item.market_hash_name in seen_names:
                item.price_usd = round(seen_names[item.market_hash_name], 2)

        logger.info(f"Lis-Skins: scraped {len(items)} unique items")
        return items
