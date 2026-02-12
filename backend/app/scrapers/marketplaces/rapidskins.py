"""RapidSkins.com scraper - uses official API (api.rapidskins.com/docs).

API requires an API key. Set RAPIDSKINS_API_KEY env var.
Prices are in cents ($1 USD = 100 cents).
Swagger: https://api.rapidskins.com/docs/swagger.json
"""

import logging

from app.config import settings
from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class RapidSkinsScraper(BaseScraper):
    marketplace_slug = "rapidskins"
    marketplace_name = "RapidSkins"
    scraper_type = "api"

    # Official API: GET /stock/assets/list
    # Docs: https://api.rapidskins.com/docs
    API_URL = "https://api.rapidskins.com/api/v1/stock/assets/list"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        seen_names: dict[str, float] = {}

        api_key = getattr(settings, "RAPIDSKINS_API_KEY", "")

        headers = {"Accept": "application/json"}
        params = {"appId": "730"}

        if api_key:
            headers["x-api-key"] = api_key
        else:
            logger.warning("RapidSkins: no API key configured (RAPIDSKINS_API_KEY)")

        data = await fetch_json(self.API_URL, headers=headers, params=params)
        if not data:
            logger.error("RapidSkins: no data returned")
            return items

        # Response: { items: [...], totalCount: N }
        results = data.get("items", data.get("data", []))

        for item in results:
            try:
                name = item.get("marketHashName") or item.get("market_hash_name") or item.get("name", "")
                # Prices in cents
                price = item.get("price", 0)
                if isinstance(price, str):
                    try:
                        price = float(price)
                    except ValueError:
                        continue

                if isinstance(price, (int, float)) and price > 100:
                    price = price / 100  # Convert cents to dollars

                if not name or price <= 0:
                    continue

                # Deduplicate — keep cheapest
                if name in seen_names:
                    if price < seen_names[name]:
                        seen_names[name] = price
                    continue

                seen_names[name] = price

                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    item_type=classify_item_type(name),
                ))
            except Exception as e:
                logger.debug(f"RapidSkins: error parsing item: {e}")
                continue

        # Update prices for deduplicated items
        for item in items:
            if item.market_hash_name in seen_names:
                item.price_usd = round(seen_names[item.market_hash_name], 2)

        logger.info(f"RapidSkins: scraped {len(items)} unique items")
        return items
