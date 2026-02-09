from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), index=True, nullable=False)
    marketplace_id: Mapped[int] = mapped_column(Integer, ForeignKey("marketplaces.id"), index=True, nullable=False)
    price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    listing_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    item: Mapped["Item"] = relationship("Item")
    marketplace: Mapped["Marketplace"] = relationship("Marketplace")
