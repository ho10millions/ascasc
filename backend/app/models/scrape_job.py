import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    marketplace_id: Mapped[int] = mapped_column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    items_scraped: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(20), default="scheduler")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    marketplace: Mapped["Marketplace"] = relationship("Marketplace")
