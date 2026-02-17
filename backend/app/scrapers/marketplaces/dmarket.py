"""DMarket.com scraper - uses public API (no auth required).

Prices are in cents as strings, e.g. {"USD": "245"} = $2.45.
Docs: https://docs.dmarket.com/v1/swagger.html
"""

import asyncio
import logging

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class DMarketScraper(BaseScraper):
    marketplace_slug = "dmarket"
    marketplace_name = "DMarket"
    scraper_type = "api"

    API_URL = "https://api.dmarket.com/exchange/v1/market/items"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        cursor = ""
        seen_names: dict[str, float] = {}

        for page in range(50):  # Max 50 pages
            params = {
                "side": "market",
                "orderBy": "price",
                "orderDir": "asc",
                "gameId": "a8db",  # CS2 game ID on DMarket
                "limit": "100",
                "currency": "USD",
            }
            if cursor:
                params["cursor"] = cursor

            data = await fetch_json(self.API_URL, params=params)
            if not data:
                break

            objects = data.get("objects", [])
            if not objects:
                break

            for obj in objects:
                try:
                    name = obj.get("title", "")
                    if not name:
                        continue

                    price_data = obj.get("price", {})
                    # DMarket returns prices in cents as strings, e.g. {"USD": "245"}
                    raw_price = price_data.get("USD", "0")
                    try:
                        price = float(raw_price) / 100
                    except (ValueError, TypeError):
                        continue

                    if price <= 0:
                        continue

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
                        icon_url=obj.get("image"),
                        item_type=classify_item_type(name),
                    ))
                except Exception as e:
                    logger.debug(f"DMarket: error parsing item: {e}")
                    continue

            cursor = data.get("cursor", "")
            if not cursor:
                break

            # Rate limit: small delay between pages
            await asyncio.sleep(0.5)

        # Update prices for deduplicated items
        for item in items:
            if item.market_hash_name in seen_names:
                item.price_usd = round(seen_names[item.market_hash_name], 2)

        logger.info(f"DMarket: scraped {len(items)} unique items")
        return items
