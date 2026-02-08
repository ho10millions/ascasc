import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import Marketplace
from app.models.price import PriceSnapshot


async def save_price_snapshot(
    db: AsyncSession,
    item_id: uuid.UUID,
    marketplace_id: int,
    price_usd: float,
    listing_count: int | None = None,
) -> PriceSnapshot:
    snapshot = PriceSnapshot(
        item_id=item_id,
        marketplace_id=marketplace_id,
        price_usd=price_usd,
        listing_count=listing_count,
    )
    db.add(snapshot)
    await db.flush()
    return snapshot


async def get_latest_steam_price(db: AsyncSession, item_id: uuid.UUID) -> float | None:
    """Get the latest Steam price for an item."""
    steam_mkt = await db.execute(
        select(Marketplace).where(Marketplace.slug == "steam")
    )
    steam = steam_mkt.scalar_one_or_none()
    if not steam:
        return None

    result = await db.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.item_id == item_id, PriceSnapshot.marketplace_id == steam.id)
        .order_by(PriceSnapshot.scraped_at.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()
    return float(snapshot.price_usd) if snapshot else None


async def get_price_history(
    db: AsyncSession,
    item_id: uuid.UUID,
    marketplace_id: int | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> list[PriceSnapshot]:
    query = select(PriceSnapshot).where(PriceSnapshot.item_id == item_id)

    if marketplace_id:
        query = query.where(PriceSnapshot.marketplace_id == marketplace_id)
    if since:
        query = query.where(PriceSnapshot.scraped_at >= since)

    query = query.order_by(PriceSnapshot.scraped_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
