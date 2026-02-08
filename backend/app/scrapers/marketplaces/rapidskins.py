"""RapidSkins.com scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class RapidSkinsScraper(BaseScraper):
    marketplace_slug = "rapidskins"
    marketplace_name = "RapidSkins"
    scraper_type = "api"

    API_URL = "https://rapidskins.com/api/inventory"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        data = await fetch_json(
            self.API_URL, params={"game": "csgo", "limit": 500, "sort": "price_asc"},
        )
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
            if isinstance(price, (int, float)) and price > 10000:
                price = price / 100
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
