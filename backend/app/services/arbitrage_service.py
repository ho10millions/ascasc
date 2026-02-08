import math
import uuid

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arbitrage import ArbitrageOpportunity
from app.models.item import Item
from app.models.marketplace import Marketplace
from app.models.price import PriceSnapshot
from app.schemas.arbitrage import ArbitrageFilters

STEAM_FEE_MULTIPLIER = 0.87  # Steam takes ~13% commission


async def calculate_arbitrage_for_item(
    db: AsyncSession, item_id: uuid.UUID, steam_price: float
) -> list[ArbitrageOpportunity]:
    """Calculate arbitrage opportunities for an item against all marketplaces."""
    steam_after_fee = steam_price * STEAM_FEE_MULTIPLIER

    # Deactivate old opportunities for this item
    await db.execute(
        ArbitrageOpportunity.__table__.update()
        .where(ArbitrageOpportunity.item_id == item_id)
        .values(is_active=False)
    )

    # Get latest prices from non-Steam marketplaces
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
            and_(
                PriceSnapshot.marketplace_id == latest_sub.c.marketplace_id,
                PriceSnapshot.scraped_at == latest_sub.c.max_time,
            ),
        )
        .where(
            PriceSnapshot.item_id == item_id,
            Marketplace.slug != "steam",
        )
    )

    results = (await db.execute(query)).all()
    opportunities = []

    for snapshot, marketplace in results:
        buy_price = float(snapshot.price_usd)
        if buy_price <= 0:
            continue

        profit_usd = steam_after_fee - buy_price
        profit_pct = ((steam_after_fee / buy_price) - 1) * 100

        if profit_pct >= 0:  # Store all positive opportunities, filter in queries
            opp = ArbitrageOpportunity(
                item_id=item_id,
                buy_marketplace_id=marketplace.id,
                buy_price_usd=buy_price,
                steam_price_usd=steam_price,
                steam_price_after_fee=steam_after_fee,
                profit_usd=round(profit_usd, 2),
                profit_pct=round(profit_pct, 2),
                is_active=True,
            )
            db.add(opp)
            opportunities.append(opp)

    await db.flush()
    return opportunities


async def get_arbitrage_opportunities(
    db: AsyncSession, filters: ArbitrageFilters
) -> tuple[list[dict], int]:
    """Get filtered and paginated arbitrage opportunities."""
    base_where = [ArbitrageOpportunity.is_active.is_(True)]

    if filters.min_profit_pct > 0:
        base_where.append(ArbitrageOpportunity.profit_pct >= filters.min_profit_pct)
    if filters.max_profit_pct is not None:
        base_where.append(ArbitrageOpportunity.profit_pct <= filters.max_profit_pct)

    # Join conditions
    query = (
        select(ArbitrageOpportunity, Item, Marketplace)
        .join(Item, ArbitrageOpportunity.item_id == Item.id)
        .join(Marketplace, ArbitrageOpportunity.buy_marketplace_id == Marketplace.id)
        .where(*base_where)
    )
    count_query = (
        select(func.count(ArbitrageOpportunity.id))
        .join(Item, ArbitrageOpportunity.item_id == Item.id)
        .join(Marketplace, ArbitrageOpportunity.buy_marketplace_id == Marketplace.id)
        .where(*base_where)
    )

    # Additional filters
    if filters.game:
        query = query.where(Item.game == filters.game)
        count_query = count_query.where(Item.game == filters.game)
    if filters.item_type:
        query = query.where(Item.item_type == filters.item_type)
        count_query = count_query.where(Item.item_type == filters.item_type)
    if filters.min_price is not None:
        query = query.where(ArbitrageOpportunity.buy_price_usd >= filters.min_price)
        count_query = count_query.where(ArbitrageOpportunity.buy_price_usd >= filters.min_price)
    if filters.max_price is not None:
        query = query.where(ArbitrageOpportunity.buy_price_usd <= filters.max_price)
        count_query = count_query.where(ArbitrageOpportunity.buy_price_usd <= filters.max_price)
    if filters.marketplace_slug:
        query = query.where(Marketplace.slug == filters.marketplace_slug)
        count_query = count_query.where(Marketplace.slug == filters.marketplace_slug)
    if filters.search:
        query = query.where(Item.market_hash_name.ilike(f"%{filters.search}%"))
        count_query = count_query.where(Item.market_hash_name.ilike(f"%{filters.search}%"))

    # Sorting
    sort_col_map = {
        "profit_pct": ArbitrageOpportunity.profit_pct,
        "profit_usd": ArbitrageOpportunity.profit_usd,
        "buy_price": ArbitrageOpportunity.buy_price_usd,
        "steam_price": ArbitrageOpportunity.steam_price_usd,
        "detected_at": ArbitrageOpportunity.detected_at,
        "name": Item.market_hash_name,
    }
    sort_col = sort_col_map.get(filters.sort_by, ArbitrageOpportunity.profit_pct)
    if filters.sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = (await db.execute(count_query)).scalar() or 0

    query = query.offset((filters.page - 1) * filters.per_page).limit(filters.per_page)
    results = (await db.execute(query)).all()

    items = []
    for opp, item, marketplace in results:
        items.append({
            "id": opp.id,
            "item_id": item.id,
            "market_hash_name": item.market_hash_name,
            "game": item.game,
            "icon_url": item.icon_url,
            "item_type": item.item_type,
            "buy_marketplace_name": marketplace.name,
            "buy_marketplace_slug": marketplace.slug,
            "buy_marketplace_url": marketplace.base_url,
            "buy_price_usd": float(opp.buy_price_usd),
            "steam_price_usd": float(opp.steam_price_usd),
            "steam_price_after_fee": float(opp.steam_price_after_fee),
            "profit_usd": float(opp.profit_usd),
            "profit_pct": float(opp.profit_pct),
            "is_active": opp.is_active,
            "detected_at": opp.detected_at,
        })

    return items, total


async def get_arbitrage_stats(db: AsyncSession) -> dict:
    """Get summary statistics for the dashboard."""
    active_count = (
        await db.execute(
            select(func.count(ArbitrageOpportunity.id)).where(
                ArbitrageOpportunity.is_active.is_(True)
            )
        )
    ).scalar() or 0

    high_value_count = (
        await db.execute(
            select(func.count(ArbitrageOpportunity.id)).where(
                ArbitrageOpportunity.is_active.is_(True),
                ArbitrageOpportunity.profit_pct >= 50,
            )
        )
    ).scalar() or 0

    avg_profit = (
        await db.execute(
            select(func.avg(ArbitrageOpportunity.profit_pct)).where(
                ArbitrageOpportunity.is_active.is_(True)
            )
        )
    ).scalar()

    max_profit = (
        await db.execute(
            select(func.max(ArbitrageOpportunity.profit_pct)).where(
                ArbitrageOpportunity.is_active.is_(True)
            )
        )
    ).scalar()

    total_items = (await db.execute(select(func.count(Item.id)))).scalar() or 0

    return {
        "active_opportunities": active_count,
        "high_value_opportunities": high_value_count,
        "avg_profit_pct": round(float(avg_profit), 2) if avg_profit else 0,
        "max_profit_pct": round(float(max_profit), 2) if max_profit else 0,
        "total_items_tracked": total_items,
    }
