from datetime import datetime

from pydantic import BaseModel, Field


class ArbitrageResponse(BaseModel):
    id: int
    item_id: str
    market_hash_name: str
    game: str
    icon_url: str | None
    item_type: str | None
    buy_marketplace_name: str
    buy_marketplace_slug: str
    buy_marketplace_url: str
    steam_url: str
    buy_price_usd: float
    steam_price_usd: float
    steam_price_after_fee: float
    profit_usd: float
    profit_pct: float
    is_active: bool
    detected_at: datetime

    model_config = {"from_attributes": True}


class ArbitrageFilters(BaseModel):
    min_profit_pct: float = Field(default=0, ge=0)
    max_profit_pct: float | None = None
    game: str | None = None
    item_type: str | None = None
    min_price: float | None = None
    max_price: float | None = None
    marketplace_slug: str | None = None
    search: str | None = None
    sort_by: str = "profit_pct"
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=50, ge=1, le=200)
