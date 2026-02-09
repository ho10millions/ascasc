import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    market_hash_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rarity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
