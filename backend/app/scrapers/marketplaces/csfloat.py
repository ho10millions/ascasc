"""CSFloat.com scraper - uses public API."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class CSFloatScraper(BaseScraper):
    marketplace_slug = "csfloat"
    marketplace_name = "CSFloat"
    scraper_type = "api"

    API_URL = "https://csfloat.com/api/v1/listings"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        seen_names = set()
        page = 0

        while page < 50:
            data = await fetch_json(
                self.API_URL,
                params={
                    "limit": 50,
                    "page": page,
                    "sort_by": "lowest_price",
                    "category": 0,
                },
            )
            if not data:
                break

            results = data if isinstance(data, list) else data.get("data", [])
            if not results:
                break

            for listing in results:
                item_data = listing.get("item", listing)
                name = item_data.get("market_hash_name", "")
                price = listing.get("price", 0)

                # CSFloat prices are in cents
                if isinstance(price, (int, float)):
                    price = price / 100

                if not name or price <= 0 or name in seen_names:
                    continue

                seen_names.add(name)
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    icon_url=item_data.get("icon_url"),
                    item_type=classify_item_type(name),
                ))

            page += 1

        return items
