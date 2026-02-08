import uuid
from datetime import datetime

from pydantic import BaseModel


class PriceSnapshotResponse(BaseModel):
    id: int
    item_id: uuid.UUID
    marketplace_id: int
    marketplace_name: str | None = None
    marketplace_slug: str | None = None
    price_usd: float
    listing_count: int | None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class PriceComparisonEntry(BaseModel):
    marketplace_name: str
    marketplace_slug: str
    price_usd: float
    listing_count: int | None
    scraped_at: datetime
    marketplace_url: str


class ItemPriceComparison(BaseModel):
    item_id: uuid.UUID
    market_hash_name: str
    game: str
    steam_price: float | None
    steam_price_after_fee: float | None
    prices: list[PriceComparisonEntry]
