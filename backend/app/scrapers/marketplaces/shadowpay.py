"""ShadowPay.com scraper - uses official API v3 (doc.shadowpay.com).

Some endpoints require API key. Set SHADOWPAY_API_KEY env var.
"""

import logging

from app.config import settings
from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class ShadowPayScraper(BaseScraper):
    marketplace_slug = "shadowpay"
    marketplace_name = "ShadowPay"
    scraper_type = "api"

    # V3 API for market items on sale
    API_URL = "https://api.shadowpay.com/api/v3/user/items/on_sale"
    # Fallback: v2 prices endpoint
    PRICES_URL = "https://api.shadowpay.com/api/v2/user/items/prices"

    async def scrape(self) -> list[ScrapedItem]:
        items = []

        api_key = getattr(settings, "SHADOWPAY_API_KEY", "")
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        # Try v3 on_sale endpoint first
        offset = 0
        limit = 100

        while offset < 5000:
            data = await fetch_json(
                self.API_URL,
                params={"project": "csgo", "limit": limit, "offset": offset},
                headers=headers if headers else None,
            )

            if not data:
                # Fallback to v2 prices on first page failure
                if offset == 0:
                    logger.info("ShadowPay: v3 failed, trying v2 prices endpoint")
                    return await self._scrape_v2(headers)
                break

            results = data.get("data", data.get("items", []))
            if not results:
                break

            for item in results:
                name = item.get("steam_market_hash_name") or item.get("market_hash_name") or item.get("name", "")
                price = item.get("price_market_min") or item.get("price") or item.get("suggested_price", 0)
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
                    icon_url=item.get("icon") or item.get("icon_url") or item.get("image"),
                    item_type=classify_item_type(name),
                ))

            offset += limit

        logger.info(f"ShadowPay: scraped {len(items)} items")
        return items

    async def _scrape_v2(self, headers: dict) -> list[ScrapedItem]:
        """Fallback: use v2 prices endpoint."""
        items = []
        offset = 0
        limit = 100

        while offset < 5000:
            data = await fetch_json(
                self.PRICES_URL,
                params={"project": "csgo", "limit": limit, "offset": offset},
                headers=headers if headers else None,
            )
            if not data:
                break

            results = data.get("data", [])
            if not results:
                break

            for item in results:
                name = item.get("steam_market_hash_name") or item.get("name", "")
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

        logger.info(f"ShadowPay (v2 fallback): scraped {len(items)} items")
        return items
