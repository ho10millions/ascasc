"""SkinSwap.com scraper - uses public API."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class SkinSwapScraper(BaseScraper):
    marketplace_slug = "skinswap"
    marketplace_name = "SkinSwap"
    scraper_type = "api"

    API_URL = "https://skinswap.com/api/v1/items"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        page = 1
        while page <= 50:
            data = await fetch_json(
                self.API_URL,
                params={"page": page, "limit": 100, "sort": "price_asc"},
            )
            if not data or not isinstance(data, dict):
                break

            results = data.get("data", data.get("items", []))
            if not results:
                break

            for item in results:
                name = item.get("market_hash_name") or item.get("name", "")
                price = item.get("price") or item.get("suggested_price", 0)
                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        continue
                # Convert cents to dollars if needed
                if price > 10000:
                    price = price / 100

                if not name or price <= 0:
                    continue

                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(price, 2),
                    game=item.get("app_name", "cs2").lower().replace("cs:go", "cs2"),
                    icon_url=item.get("icon_url") or item.get("image"),
                    item_type=classify_item_type(name),
                ))

            page += 1

        return items
