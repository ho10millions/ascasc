"""DMarket.com scraper - uses public API."""

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

        for _ in range(50):  # Max 50 pages
            params = {
                "side": "market",
                "orderBy": "price",
                "orderDir": "asc",
                "title": "",
                "priceFrom": 0,
                "priceTo": 0,
                "gameId": "a8db",  # CS2 game ID on DMarket
                "limit": 100,
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
                price_data = obj.get("price", {})
                price = float(price_data.get("USD", 0)) / 100 if price_data.get("USD") else 0

                if not name or price <= 0:
                    continue

                extra = obj.get("extra", {})
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

        return items
