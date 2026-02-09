from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ArbitrageOpportunity(Base):
    __tablename__ = "arbitrage_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[str] = mapped_column(String(36), ForeignKey("items.id"), index=True, nullable=False)
    buy_marketplace_id: Mapped[int] = mapped_column(Integer, ForeignKey("marketplaces.id"), nullable=False)
    buy_price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    steam_price_usd: Mapped[float] = mapped_column(Float, nullable=False)
    steam_price_after_fee: Mapped[float] = mapped_column(Float, nullable=False)
    profit_usd: Mapped[float] = mapped_column(Float, nullable=False)
    profit_pct: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    item: Mapped["Item"] = relationship("Item")
    buy_marketplace: Mapped["Marketplace"] = relationship("Marketplace")
