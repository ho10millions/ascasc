from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Marketplace(Base):
    __tablename__ = "marketplaces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    scraper_type: Mapped[str] = mapped_column(String(20), default="api")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    scrape_interval_minutes: Mapped[int] = mapped_column(Integer, default=30)
    last_scraped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
