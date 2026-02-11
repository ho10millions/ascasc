"""CS.Money scraper - uses active-offers API with cookie auth."""

import logging

from app.config import settings
from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class CSMoneyScraper(BaseScraper):
    marketplace_slug = "cs-money"
    marketplace_name = "CS.Money"
    scraper_type = "api"

    API_URL = "https://cs.money/1.0/market/active-offers"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        seen_names: dict[str, float] = {}

        cookies = settings.CS_MONEY_COOKIES or None
        if not cookies:
            logger.warning("CS.Money: no cookies configured — will likely get 403")
            return items

        logger.info("CS.Money: using cookie-based authentication")

        # CS.Money active-offers uses updatedFrom timestamp for pagination
        # updatedFrom=0 returns all active offers
        extra_headers = {
            "Referer": "https://cs.money/market/buy/",
            "Origin": "https://cs.money",
            "Accept": "application/json, text/plain, */*",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

        data = await fetch_json(
            self.API_URL,
            params={"updatedFrom": "0"},
            headers=extra_headers,
            cookies=cookies,
        )

        if not data:
            logger.error("CS.Money: no data returned (likely 403 — cookies/cf_clearance expired)")
            return items

        # Response can be a list or a dict with items
        offers = []
        if isinstance(data, list):
            offers = data
        elif isinstance(data, dict):
            offers = data.get("offers", data.get("items", data.get("data", [])))
            if not offers and not any(k in data for k in ("offers", "items", "data")):
                # Maybe the dict itself contains offer-like data at top level
                logger.info(f"CS.Money: response keys: {list(data.keys())[:20]}")

        logger.info(f"CS.Money: got {len(offers)} raw offers")

        for item in offers:
            try:
                name = self._extract_name(item)
                price = self._extract_price(item)

                if not name or price <= 0:
                    continue

                # Deduplicate — keep cheapest price per item name
                if name in seen_names:
                    if price < seen_names[name]:
                        seen_names[name] = price
                    continue

                seen_names[name] = price

                img = self._extract_image(item)

                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    icon_url=img,
                    item_type=classify_item_type(name),
                ))
            except Exception as e:
                logger.debug(f"CS.Money: error parsing item: {e}")
                continue

        # Update prices for deduplicated items
        for item in items:
            if item.market_hash_name in seen_names:
                item.price_usd = round(seen_names[item.market_hash_name], 2)

        logger.info(f"CS.Money: scraped {len(items)} unique items")
        return items

    def _extract_name(self, item: dict) -> str:
        """Try multiple paths to find item name."""
        # Try nested asset.names.full
        asset = item.get("asset", {})
        if isinstance(asset, dict):
            names = asset.get("names", {})
            if isinstance(names, dict) and names.get("full"):
                return names["full"]
            if asset.get("market_hash_name"):
                return asset["market_hash_name"]
            if asset.get("name"):
                return asset["name"]

        # Try direct fields
        for key in ("market_hash_name", "marketHashName", "name", "fullName", "full_name"):
            if item.get(key):
                return item[key]

        return ""

    def _extract_price(self, item: dict) -> float:
        """Try multiple paths to find price."""
        # Try pricing.computed
        pricing = item.get("pricing", {})
        if isinstance(pricing, dict):
            for key in ("computed", "default", "price", "amount"):
                val = pricing.get(key)
                if val is not None:
                    return float(val)

        # Try direct price fields
        for key in ("price", "priceUsd", "price_usd", "amount", "cost"):
            val = item.get(key)
            if val is not None:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    continue

        return 0.0

    def _extract_image(self, item: dict) -> str | None:
        """Try multiple paths to find image URL."""
        asset = item.get("asset", {})
        if isinstance(asset, dict):
            for key in ("image", "img", "icon_url", "iconUrl"):
                if asset.get(key):
                    return asset[key]

        for key in ("image", "img", "icon_url", "iconUrl"):
            if item.get(key):
                return item[key]

        return None
