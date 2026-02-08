import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.models.marketplace import Marketplace
from app.models.price import PriceSnapshot


async def get_or_create_item(
    db: AsyncSession,
    game: str,
    market_hash_name: str,
    icon_url: str | None = None,
    item_type: str | None = None,
    rarity: str | None = None,
) -> Item:
    result = await db.execute(
        select(Item).where(Item.game == game, Item.market_hash_name == market_hash_name)
    )
    item = result.scalar_one_or_none()

    if item:
        if icon_url and not item.icon_url:
            item.icon_url = icon_url
        if item_type and not item.item_type:
            item.item_type = item_type
        return item

    item = Item(
        game=game,
        market_hash_name=market_hash_name,
        icon_url=icon_url,
        item_type=item_type,
        rarity=rarity,
    )
    db.add(item)
    await db.flush()
    return item


async def get_items(
    db: AsyncSession,
    game: str | None = None,
    item_type: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> tuple[list[Item], int]:
    query = select(Item)
    count_query = select(func.count(Item.id))

    if game:
        query = query.where(Item.game == game)
        count_query = count_query.where(Item.game == game)
    if item_type:
        query = query.where(Item.item_type == item_type)
        count_query = count_query.where(Item.item_type == item_type)
    if search:
        query = query.where(Item.market_hash_name.ilike(f"%{search}%"))
        count_query = count_query.where(Item.market_hash_name.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar() or 0
    items = (
        (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).scalars().all()
    )

    return list(items), total


async def get_item_by_id(db: AsyncSession, item_id: uuid.UUID) -> Item | None:
    result = await db.execute(select(Item).where(Item.id == item_id))
    return result.scalar_one_or_none()


async def get_item_prices(
    db: AsyncSession, item_id: uuid.UUID
) -> list[dict]:
    """Get latest price from each marketplace for an item."""
    # Subquery: latest snapshot per marketplace
    latest_sub = (
        select(
            PriceSnapshot.marketplace_id,
            func.max(PriceSnapshot.scraped_at).label("max_time"),
        )
        .where(PriceSnapshot.item_id == item_id)
        .group_by(PriceSnapshot.marketplace_id)
        .subquery()
    )

    query = (
        select(PriceSnapshot, Marketplace)
        .join(Marketplace, PriceSnapshot.marketplace_id == Marketplace.id)
        .join(
            latest_sub,
            (PriceSnapshot.marketplace_id == latest_sub.c.marketplace_id)
            & (PriceSnapshot.scraped_at == latest_sub.c.max_time),
        )
        .where(PriceSnapshot.item_id == item_id)
        .order_by(PriceSnapshot.price_usd.asc())
    )

    results = (await db.execute(query)).all()

    prices = []
    for snapshot, marketplace in results:
        prices.append({
            "marketplace_name": marketplace.name,
            "marketplace_slug": marketplace.slug,
            "marketplace_url": marketplace.base_url,
            "price_usd": float(snapshot.price_usd),
            "listing_count": snapshot.listing_count,
            "scraped_at": snapshot.scraped_at,
        })

    return prices
