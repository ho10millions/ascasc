import uuid
from datetime import datetime

from pydantic import BaseModel


class ItemResponse(BaseModel):
    id: uuid.UUID
    game: str
    market_hash_name: str
    icon_url: str | None
    item_type: str | None
    rarity: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ItemWithPrices(ItemResponse):
    best_price: float | None = None
    best_marketplace: str | None = None
    best_marketplace_slug: str | None = None
    steam_price: float | None = None
    steam_price_after_fee: float | None = None
    profit_pct: float | None = None
