"""Buff163 (buff.163.com) scraper with optional cookie auth."""

import logging

from app.config import settings
from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class Buff163Scraper(BaseScraper):
    marketplace_slug = "buff163"
    marketplace_name = "Buff163"
    scraper_type = "api"

    API_URL = "https://buff.163.com/api/market/goods"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        page = 1

        cookies = settings.BUFF163_COOKIES or None
        if cookies:
            logger.info("Buff163: using cookie-based authentication")

        while page <= 50:
            data = await fetch_json(
                self.API_URL,
                params={"game": "csgo", "page_num": page, "page_size": 80},
                headers={"Referer": "https://buff.163.com/market/csgo"},
                cookies=cookies,
            )
            if not data or data.get("code") != "OK":
                break
            goods_list = data.get("data", {}).get("items", [])
            if not goods_list:
                break
            for item in goods_list:
                name = item.get("market_hash_name") or item.get("name", "")
                sell_min = item.get("sell_min_price", "0")
                try:
                    price = float(sell_min)
                except (ValueError, TypeError):
                    continue
                # Buff163 prices are in CNY, approximate conversion
                price_usd = round(price * 0.14, 2)
                if not name or price_usd <= 0:
                    continue
                icon = item.get("goods_info", {}).get("icon_url") or item.get("icon_url")
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=price_usd,
                    game="cs2",
                    icon_url=icon,
                    item_type=classify_item_type(name),
                    listing_count=item.get("sell_num"),
                ))
            page += 1
        return items
