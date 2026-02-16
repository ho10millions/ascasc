"""CS.Trade scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class CSTradeScraper(BaseScraper):
    marketplace_slug = "cs-trade"
    marketplace_name = "CS.Trade"
    scraper_type = "api"

    API_URL = "https://cs.trade/api/items"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        data = await fetch_json(self.API_URL, params={"appid": 730, "limit": 500})
        if not data:
            return items
        results = data.get("data", data.get("items", []))
        for item in results:
            name = item.get("market_hash_name") or item.get("name", "")
            price = item.get("price") or item.get("min_price", 0)
            if isinstance(price, str):
                try:
                    price = float(price)
                except ValueError:
                    continue
            # CS.Trade prices are in cents
            if isinstance(price, (int, float)):
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
