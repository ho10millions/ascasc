"""Swap.gg scraper - uses official market API (docs.swap.gg)."""

import logging

from app.config import settings
from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)


class SwapGGScraper(BaseScraper):
    marketplace_slug = "swap-gg"
    marketplace_name = "Swap.gg"
    scraper_type = "api"

    # Official API: POST https://market-api.swap.gg/v1/sales/browse
    BROWSE_URL = "https://market-api.swap.gg/v1/sales/browse"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        seen_names: dict[str, float] = {}

        api_key = getattr(settings, "SWAP_GG_API_KEY", "")
        headers = {}
        if api_key:
            headers["Authorization"] = api_key

        offset = 0
        limit = 100
        max_pages = 50

        for page in range(max_pages):
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.BROWSE_URL,
                        json={"appId": "730", "offset": offset, "limit": limit},
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                            **headers,
                        },
                        timeout=aiohttp.ClientTimeout(total=30),
                        ssl=False,
                    ) as response:
                        if response.status != 200:
                            logger.warning(f"Swap.gg: HTTP {response.status}")
                            break
                        data = await response.json()
            except Exception as e:
                logger.error(f"Swap.gg: request error: {e}")
                break

            if not data:
                break

            results = data.get("sales", data.get("data", data.get("items", [])))
            if not results:
                break

            for item in results:
                try:
                    name = item.get("marketName") or item.get("market_hash_name") or item.get("name", "")
                    price = item.get("price") or item.get("salePrice", 0)
                    if isinstance(price, str):
                        try:
                            price = float(price)
                        except ValueError:
                            continue
                    # Swap.gg prices may be in cents
                    if isinstance(price, (int, float)) and price > 10000:
                        price = price / 100

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
                        icon_url=item.get("image") or item.get("icon_url"),
                        item_type=classify_item_type(name),
                    ))
                except Exception as e:
                    logger.debug(f"Swap.gg: error parsing item: {e}")
                    continue

            offset += limit

        # Update prices for deduplicated items
        for item in items:
            if item.market_hash_name in seen_names:
                item.price_usd = round(seen_names[item.market_hash_name], 2)

        logger.info(f"Swap.gg: scraped {len(items)} unique items")
        return items
