import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), index=True, nullable=False
    )
    marketplace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("marketplaces.id"), index=True, nullable=False
    )
    price_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    listing_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    item: Mapped["Item"] = relationship("Item")
    marketplace: Mapped["Marketplace"] = relationship("Marketplace")

    __table_args__ = (
        Index("ix_price_item_market_time", "item_id", "marketplace_id", scraped_at.desc()),
    )
