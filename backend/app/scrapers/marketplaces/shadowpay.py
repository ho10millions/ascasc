"""ShadowPay.com scraper - uses public API."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class ShadowPayScraper(BaseScraper):
    marketplace_slug = "shadowpay"
    marketplace_name = "ShadowPay"
    scraper_type = "api"

    API_URL = "https://api.shadowpay.com/api/v2/user/items/prices"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        offset = 0
        limit = 100

        while offset < 5000:
            data = await fetch_json(
                self.API_URL,
                params={"project": "csgo", "limit": limit, "offset": offset},
            )
            if not data:
                break

            results = data.get("data", [])
            if not results:
                break

            for item in results:
                name = item.get("steam_market_hash_name", "")
                price = item.get("price_market_min") or item.get("price", 0)
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
                    icon_url=item.get("icon"),
                    item_type=classify_item_type(name),
                ))

            offset += limit

        return items
