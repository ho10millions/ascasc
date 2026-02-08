"""Loot.Farm scraper."""

from app.scrapers.base import BaseScraper, ScrapedItem
from app.scrapers.utils import fetch_json, classify_item_type


class LootFarmScraper(BaseScraper):
    marketplace_slug = "loot-farm"
    marketplace_name = "Loot.Farm"
    scraper_type = "api"

    API_URL = "https://loot.farm/fullprice.json"

    async def scrape(self) -> list[ScrapedItem]:
        items = []
        data = await fetch_json(self.API_URL)
        if not data:
            return items

        # Loot.Farm returns {game: {item_name: price_in_cents}}
        cs_data = data.get("730", data) if isinstance(data, dict) else data
        if isinstance(cs_data, dict):
            for name, price_cents in cs_data.items():
                if isinstance(price_cents, dict):
                    price_cents = price_cents.get("price", 0)
                try:
                    price = float(price_cents) / 100
                except (ValueError, TypeError):
                    continue
                if price <= 0:
                    continue
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(price, 2),
                    game="cs2",
                    item_type=classify_item_type(name),
                ))
        elif isinstance(cs_data, list):
            for item in cs_data:
                name = item.get("name", "")
                price = item.get("price", 0)
                if isinstance(price, (int, float)) and price > 1000:
                    price = price / 100
                if not name or price <= 0:
                    continue
                items.append(ScrapedItem(
                    market_hash_name=name,
                    price_usd=round(float(price), 2),
                    game="cs2",
                    item_type=classify_item_type(name),
                ))
        return items
