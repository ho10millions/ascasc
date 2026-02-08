"""Youpin898.com scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class Youpin898Scraper(BaseScraper):
    marketplace_slug = "youpin898"
    marketplace_name = "Youpin898"
    scraper_type = "api"

    API_URL = "https://api.youpin898.com/api/homepage/es/template/GetCsGoPagedList"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        page = 1
        while page <= 50:
            data = await fetch_json(
                self.API_URL,
                params={"gameId": "csgo", "pageIndex": page, "pageSize": 100},
            )
            if not data:
                break
            results = data.get("Data", data.get("data", []))
            if isinstance(results, dict):
                results = results.get("list", results.get("items", []))
            if not results:
                break
            for item in results:
                name = item.get("MarketHashName") or item.get("market_hash_name") or item.get("name", "")
                price = item.get("Price") or item.get("price", 0)
                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        continue
                # Youpin prices in CNY
                price_usd = round(float(price) * 0.14, 2)
                if not name or price_usd <= 0:
                    continue
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=price_usd,
                    game="cs2",
                    icon_url=item.get("IconUrl") or item.get("icon_url"),
                    item_type=classify_item_type(name),
                ))
            page += 1
        return items
