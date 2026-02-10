"""DMarket.com scraper - uses public API (no auth required)."""

import asyncio

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class DMarketScraper(BaseScraper):
    marketplace_slug = "dmarket"
    marketplace_name = "DMarket"
    scraper_type = "api"

    API_URL = "https://api.dmarket.com/exchange/v1/market/items"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        cursor = ""
        seen_names: set[str] = set()

        for _ in range(50):  # Max 50 pages
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
                name = obj.get("title", "")
                if not name or name in seen_names:
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

                seen_names.add(name)
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(price, 2),
                    game="cs2",
                    icon_url=obj.get("image"),
                    item_type=classify_item_type(name),
                ))

            cursor = data.get("cursor", "")
            if not cursor:
                break

            # Rate limit: small delay between pages
            await asyncio.sleep(0.5)

        return items
