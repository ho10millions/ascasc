"""Avan.Market scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class AvanMarketScraper(BaseScraper):
    marketplace_slug = "avan-market"
    marketplace_name = "Avan Market"
    scraper_type = "playwright"

    API_URL = "https://avan.market/api/items"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        data = await fetch_json(self.API_URL, params={"game": "csgo", "limit": 500})
        if not data:
            return items
        results = data.get("data", data.get("items", []))
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
                icon_url=item.get("icon_url") or item.get("image"),
                item_type=classify_item_type(name),
            ))
        return items
