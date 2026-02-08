import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # cs2, dota2, tf2, rust
    market_hash_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Rifle, Knife, Gloves, etc.
    rarity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        # Unique constraint: same name in same game
        {"sqlite_autoincrement": False},
    )
