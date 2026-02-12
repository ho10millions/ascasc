"""Skinout.gg scraper - uses official Skinout Pay API (docs.skinout.gg).

API requires an API key. Get one from docs.skinout.gg/en/sign.
Set SKINOUT_API_KEY and SKINOUT_PROJECT_ID env vars.
Prices returned in USD × 1000 format (e.g., 615425 = $615.425).
"""

import logging

import aiohttp

from app.config import settings
from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import classify_item_type

logger = logging.getLogger(__name__)

# Top CS2 weapon names to search (Skinout requires name-based search)
TOP_CS2_ITEMS = [
    "AK-47", "M4A4", "M4A1-S", "AWP", "Desert Eagle", "USP-S", "Glock-18",
    "Karambit", "Butterfly Knife", "Bayonet", "Talon Knife", "Skeleton Knife",
    "Sport Gloves", "Specialist Gloves", "Driver Gloves", "Hand Wraps",
    "P250", "Five-SeveN", "P90", "MP9", "MAC-10", "UMP-45",
    "SSG 08", "SCAR-20", "Nova", "XM1014", "Negev",
]


class SkinoutScraper(BaseScraper):
    marketplace_slug = "skinout-gg"
    marketplace_name = "Skinout.gg"
    scraper_type = "api"

    # Official API: POST /withdraw/search
    # Docs: https://docs.skinout.gg/withdraw-skins/skins-search
    SEARCH_URL = "https://pay.skinout.gg/api/v1/withdraw/search"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        seen_names: dict[str, float] = {}

        api_key = getattr(settings, "SKINOUT_API_KEY", "")
        project_id = getattr(settings, "SKINOUT_PROJECT_ID", "")

        if not api_key:
            logger.warning("Skinout.gg: no API key configured (SKINOUT_API_KEY)")
            return items

        headers = {
            "Content-Type": "application/json",
            "Api-Key": api_key,
        }

        for weapon_name in TOP_CS2_ITEMS:
            try:
                async with aiohttp.ClientSession() as session:
                    body = {"name": weapon_name}
                    if project_id:
                        body["project_id"] = project_id

                    async with session.post(
                        self.SEARCH_URL,
                        json=body,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                        ssl=False,
                    ) as response:
                        if response.status != 200:
                            logger.debug(f"Skinout.gg: HTTP {response.status} for {weapon_name}")
                            continue
                        data = await response.json()
            except Exception as e:
                logger.debug(f"Skinout.gg: request error for {weapon_name}: {e}")
                continue

            if not data or not data.get("success"):
                continue

            skins = data.get("skins", [])
            for skin in skins:
                try:
                    name = skin.get("name", "")
                    # Price is in USD × 1000
                    raw_price = skin.get("price", 0)
                    if not name or not raw_price:
                        continue

                    price = float(raw_price) / 1000

                    if price <= 0:
                        continue

                    if name in seen_names:
                        if price < seen_names[name]:
                            seen_names[name] = price
                        continue

                    seen_names[name] = price

                    items.append(ScrapedItem(
                        market_hash_name=name,
                        price_usd=round(price, 2),
                        game="cs2",
                        item_type=classify_item_type(name),
                    ))
                except Exception as e:
                    logger.debug(f"Skinout.gg: error parsing skin: {e}")
                    continue

        # Update prices for deduplicated items
        for item in items:
            if item.market_hash_name in seen_names:
                item.price_usd = round(seen_names[item.market_hash_name], 2)

        logger.info(f"Skinout.gg: scraped {len(items)} unique items")
        return items
