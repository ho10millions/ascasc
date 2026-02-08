"""CS.Money scraper - uses API endpoints."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class CSMoneyScraper(BaseScraper):
    marketplace_slug = "cs-money"
    marketplace_name = "CS.Money"
    scraper_type = "api"

    API_URL = "https://cs.money/1.0/market/sell-orders"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        offset = 0
        limit = 60

        while offset < 5000:
            data = await fetch_json(
                self.API_URL,
                params={
                    "limit": limit,
                    "offset": offset,
                    "sort": "price",
                    "order": "asc",
                },
            )
            if not data:
                break

            results = data.get("items", data.get("data", []))
            if not results:
                break

            for item in results:
                name_info = item.get("asset", item)
                name = name_info.get("names", {}).get("full", "") or item.get("name", "")
                if not name:
                    name = name_info.get("market_hash_name", "")
                price = item.get("pricing", {}).get("computed", item.get("price", 0))

                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        continue

                if not name or price <= 0:
                    continue

                img = name_info.get("image") or item.get("img") or item.get("icon_url")

                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    icon_url=img,
                    item_type=classify_item_type(name),
                ))

            offset += limit

        return items
