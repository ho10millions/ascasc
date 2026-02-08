"""Market.CSGO.com scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class MarketCSGOScraper(BaseScraper):
    marketplace_slug = "market-csgo"
    marketplace_name = "Market CSGO"
    scraper_type = "api"

    API_URL = "https://market.csgo.com/api/v2/prices/USD.json"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        data = await fetch_json(self.API_URL)
        if not data:
            return items

        results = data.get("items", data.get("data", []))
        if isinstance(results, dict):
            for name, info in results.items():
                price = info.get("price") if isinstance(info, dict) else info
                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        continue
                if not isinstance(price, (int, float)) or price <= 0:
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
