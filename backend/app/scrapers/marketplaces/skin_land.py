"""Skin.Land scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class SkinLandScraper(BaseScraper):
    marketplace_slug = "skin-land"
    marketplace_name = "Skin.Land"
    scraper_type = "api"

    API_URL = "https://skin.land/api/v1/items"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        page = 1
        while page <= 50:
            data = await fetch_json(
                self.API_URL, params={"page": page, "limit": 100, "game": "csgo"},
            )
            if not data:
                break
            results = data.get("data", data.get("items", []))
            if not results:
                break
            for item in results:
                name = item.get("market_hash_name") or item.get("name", "")
                price = item.get("price") or item.get("min_price", 0)
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
            page += 1
        return items
