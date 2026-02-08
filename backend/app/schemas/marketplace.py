from datetime import datetime

from pydantic import BaseModel


class MarketplaceResponse(BaseModel):
    id: int
    name: str
    slug: str
    base_url: str
    scraper_type: str
    is_enabled: bool
    scrape_interval_minutes: int
    last_scraped_at: datetime | None

    model_config = {"from_attributes": True}


class MarketplaceUpdate(BaseModel):
    is_enabled: bool | None = None
    scrape_interval_minutes: int | None = None
