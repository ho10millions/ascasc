import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marketplace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("marketplaces.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, running, completed, failed
    items_scraped: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(20), default="scheduler")  # scheduler, admin
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    marketplace: Mapped["Marketplace"] = relationship("Marketplace")
