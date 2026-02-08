"""Buff.Market scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class BuffMarketScraper(BaseScraper):
    marketplace_slug = "buff-market"
    marketplace_name = "Buff Market"
    scraper_type = "api"

    API_URL = "https://buff.market/api/market/goods"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        page = 1
        while page <= 50:
            data = await fetch_json(
                self.API_URL, params={"page": page, "page_size": 80, "game": "csgo"},
            )
            if not data:
                break
            results = data.get("data", {}).get("items", data.get("items", []))
            if not results:
                break
            for item in results:
                name = item.get("market_hash_name") or item.get("name", "")
                sell_min = item.get("sell_min_price") or item.get("price", 0)
                if isinstance(sell_min, str):
                    try:
                        sell_min = float(sell_min)
                    except ValueError:
                        continue
                if not name or sell_min <= 0:
                    continue
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(sell_min), 2),
                    game="cs2",
                    icon_url=item.get("goods_info", {}).get("icon_url") or item.get("icon_url"),
                    item_type=classify_item_type(name),
                    listing_count=item.get("sell_num"),
                ))
            page += 1
        return items
