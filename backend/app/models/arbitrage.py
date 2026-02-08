import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ArbitrageOpportunity(Base):
    __tablename__ = "arbitrage_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("items.id"), index=True, nullable=False
    )
    buy_marketplace_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("marketplaces.id"), nullable=False
    )
    buy_price_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    steam_price_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    steam_price_after_fee: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    profit_usd: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    profit_pct: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    item: Mapped["Item"] = relationship("Item")
    buy_marketplace: Mapped["Marketplace"] = relationship("Marketplace")

    __table_args__ = (
        Index("ix_arb_profit_active", "is_active", profit_pct.desc()),
    )
