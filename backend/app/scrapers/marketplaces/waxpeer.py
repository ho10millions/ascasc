"""Waxpeer.com scraper - uses public API."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class WaxpeerScraper(BaseScraper):
    marketplace_slug = "waxpeer"
    marketplace_name = "Waxpeer"
    scraper_type = "api"

    API_URL = "https://api.waxpeer.com/v1/prices"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        data = await fetch_json(
            self.API_URL,
            params={"game": "csgo", "min_price": 100, "max_price": 1000000},
        )
        if not data or not data.get("success"):
            # Try alternative endpoint
            data = await fetch_json("https://api.waxpeer.com/v1/get-items-list")

        if not data:
            return items

        results = data.get("items", data.get("data", []))
        if isinstance(results, dict):
            # Some APIs return {name: price} format
            for name, price_info in results.items():
                price = price_info if isinstance(price_info, (int, float)) else price_info.get("price", 0)
                if price > 10000:
                    price = price / 1000  # Convert from millicents
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

        return items
