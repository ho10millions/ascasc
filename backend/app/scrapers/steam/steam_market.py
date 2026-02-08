"""Steam Community Market scraper using Steam API."""

import asyncio
import logging

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type

logger = logging.getLogger(__name__)

# Steam app IDs
STEAM_APPS = {
    "cs2": 730,
    "dota2": 570,
    "tf2": 440,
    "rust": 252490,
}

STEAM_MARKET_API = "https://steamcommunity.com/market/search/render/"


class SteamMarketScraper(BaseScraper):
    marketplace_slug = "steam"
    marketplace_name = "Steam Market"
    scraper_type = "api"

    def __init__(self, games: list[str] | None = None):
        super().__init__()
        self.games = games or ["cs2", "dota2"]

    async def scrape(self) -> list[ScrapedItem]:
        all_items = []
        for game in self.games:
            app_id = STEAM_APPS.get(game)
            if not app_id:
                continue
            items = await self._scrape_game(game, app_id)
            all_items.extend(items)
        return all_items

    async def _scrape_game(self, game: str, app_id: int) -> list[ScrapedItem]:
        items = []
        start = 0
        count = 100  # Steam API max per page

        while True:
            params = {
                "appid": app_id,
                "norender": 1,
                "count": count,
                "start": start,
                "sort_column": "popular",
                "sort_dir": "desc",
            }

            data = await fetch_json(STEAM_MARKET_API, params=params)
            if not data or not data.get("success"):
                break

            results = data.get("results", [])
            if not results:
                break

            for result in results:
                name = result.get("hash_name") or result.get("name", "")
                sell_price = result.get("sell_price_text", "")
                asset_desc = result.get("asset_description", {})

                # Parse price (format: "$1.23" or "1,23€" etc)
                price = self._parse_price(sell_price)
                if not price or price <= 0:
                    continue

                icon_url = None
                if asset_desc.get("icon_url"):
                    icon_url = f"https://community.akamai.steamstatic.com/economy/image/{asset_desc['icon_url']}/128fx128f"

                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=price,
                    game=game,
                    icon_url=icon_url,
                    item_type=classify_item_type(name),
                    listing_count=result.get("sell_listings", 0),
                ))

            total_count = data.get("total_count", 0)
            start += count

            if start >= total_count or start >= 5000:  # Cap at 5000 items per game
                break

            # Rate limiting: Steam API is strict
            await asyncio.sleep(3)

        self.logger.info(f"Scraped {len(items)} items from Steam Market for {game}")
        return items

    @staticmethod
    def _parse_price(price_text: str) -> float | None:
        if not price_text:
            return None
        # Remove currency symbols and normalize
        cleaned = price_text.replace("$", "").replace("€", "").replace("£", "")
        cleaned = cleaned.replace(",", ".").replace(" ", "").strip()
        # Handle cases like "1.234,56" -> take last dot as decimal
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        try:
            return round(float(cleaned), 2)
        except ValueError:
            return None
