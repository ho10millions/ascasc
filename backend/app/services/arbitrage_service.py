from urllib.parse import quote

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arbitrage import ArbitrageOpportunity
from app.models.item import Item
from app.models.marketplace import Marketplace
from app.models.price import PriceSnapshot
from app.schemas.arbitrage import ArbitrageFilters

STEAM_FEE_MULTIPLIER = 0.87

# Game → Steam appid mapping
GAME_APPID = {"cs2": "730", "csgo": "730", "dota2": "570", "tf2": "440", "rust": "252490"}

# Marketplace slug → item page URL template
# {name} = raw name, {q} = URL-encoded name, {app} = Steam appid
ITEM_URL_PATTERNS: dict[str, str] = {
    "market-csgo": "https://market.csgo.com/?search={q}",
    "waxpeer": "https://waxpeer.com/csgo/{q}",
    "csfloat": "https://csfloat.com/search?market_hash_name={q}",
    "dmarket": "https://dmarket.com/ingame-items/item-list/csgo-skins?title={q}",
    "cs-money": "https://cs.money/market/buy/?search={q}",
    "shadowpay": "https://shadowpay.com/csgo-items?search={q}",
    "loot-farm": "https://loot.farm/",
    "buff163": "https://buff.163.com/market/csgo#tab=selling&page_num=1&search={q}",
    "buff-market": "https://buff.market/market/csgo#tab=selling&search={q}",
    "swap-gg": "https://swap.gg/csgo/market?search={q}",
    "rapidskins": "https://rapidskins.com/market/csgo?search={q}",
    "cs-trade": "https://cs.trade/?search={q}",
    "skinswap": "https://skinswap.com/csgo?search={q}",
    "white-market": "https://white.market/market/csgo?search={q}",
    "lis-skins": "https://lis-skins.com/?search={q}",
    "skins-cash": "https://skins.cash/?search={q}",
    "skins-com": "https://skins.com/market?search={q}",
    "itrade-gg": "https://itrade.gg/csgo?search={q}",
    "skincashier": "https://skincashier.com/?search={q}",
    "youpin898": "https://youpin898.com/market/csgo?search={q}",
    "skin-place": "https://skin.place/market?search={q}",
    "skin-land": "https://skin.land/market?search={q}",
    "skinomat": "https://skinomat.com/?search={q}",
    "aim-market": "https://aim.market/?search={q}",
    "avan-market": "https://avan.market/?search={q}",
    "pirateswap": "https://pirateswap.com/?search={q}",
    "moon-market": "https://moon.market/?search={q}",
    "skincantor": "https://skincantor.com/?search={q}",
    "skinout-gg": "https://skinout.gg/?search={q}",
}


def build_item_url(slug: str, base_url: str, market_hash_name: str) -> str:
    """Build a direct link to the item on a marketplace."""
    q = quote(market_hash_name, safe="")
    template = ITEM_URL_PATTERNS.get(slug)
    if template:
        return template.replace("{q}", q).replace("{name}", market_hash_name)
    return f"{base_url}?search={q}"


def build_steam_url(market_hash_name: str, game: str = "cs2") -> str:
    """Build a link to the item on Steam Market."""
    app_id = GAME_APPID.get(game, "730")
    return f"https://steamcommunity.com/market/listings/{app_id}/{quote(market_hash_name, safe='')}"


async def calculate_arbitrage_for_item(
    db: AsyncSession, item_id: str, steam_price: float
) -> list[ArbitrageOpportunity]:
    steam_after_fee = steam_price * STEAM_FEE_MULTIPLIER

    await db.execute(
        ArbitrageOpportunity.__table__.update()
        .where(ArbitrageOpportunity.item_id == item_id)
        .values(is_active=False)
    )

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

        if profit_pct >= 0:
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
    base_where = [ArbitrageOpportunity.is_active.is_(True)]

    if filters.min_profit_pct > 0:
        base_where.append(ArbitrageOpportunity.profit_pct >= filters.min_profit_pct)
    if filters.max_profit_pct is not None:
        base_where.append(ArbitrageOpportunity.profit_pct <= filters.max_profit_pct)

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
            "buy_marketplace_url": build_item_url(
                marketplace.slug, marketplace.base_url, item.market_hash_name
            ),
            "steam_url": build_steam_url(item.market_hash_name, item.game),
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
