"""Swap.gg scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class SwapGGScraper(BaseScraper):
    marketplace_slug = "swap-gg"
    marketplace_name = "Swap.gg"
    scraper_type = "api"

    API_URL = "https://api.swap.gg/v1/pricing/items"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        data = await fetch_json(self.API_URL, params={"appId": 730})
        if not data:
            return items
        results = data.get("data", data.get("items", []))
        if isinstance(results, dict):
            for name, price_info in results.items():
                price = price_info if isinstance(price_info, (int, float)) else price_info.get("price", 0)
                if isinstance(price, (int, float)) and price > 10000:
                    price = price / 100
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
                name = item.get("market_hash_name") or item.get("name", "")
                price = item.get("price", 0)
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
                    item_type=classify_item_type(name),
                ))
        return items
