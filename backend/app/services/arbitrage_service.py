from urllib.parse import quote

from sqlalchemy import func, select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.arbitrage import ArbitrageOpportunity
from app.models.item import Item
from app.models.marketplace import Marketplace
from app.models.price import PriceSnapshot
from app.schemas.arbitrage import ArbitrageFilters

STEAM_FEE_MULTIPLIER = 0.87

# Marketplace sell commission rates (approximate %)
MARKETPLACE_FEES: dict[str, float] = {
    "steam": 13.0,
    "market-csgo": 5.0,
    "waxpeer": 5.0,
    "csfloat": 2.0,
    "dmarket": 5.5,
    "cs-money": 5.0,
    "shadowpay": 5.0,
    "loot-farm": 3.0,
    "buff163": 2.5,
    "buff-market": 2.5,
    "swap-gg": 5.0,
    "youpin898": 2.5,
    "rapidskins": 5.0,
    "skinswap": 5.0,
    "cs-trade": 3.0,
    "white-market": 5.0,
    "lis-skins": 5.0,
    "skins-cash": 5.0,
    "skins-com": 5.0,
    "itrade-gg": 5.0,
    "skincashier": 5.0,
    "skin-place": 5.0,
    "skin-land": 5.0,
    "skinomat": 5.0,
    "aim-market": 5.0,
    "avan-market": 5.0,
    "pirateswap": 5.0,
    "moon-market": 5.0,
    "skincantor": 5.0,
    "skinout-gg": 5.0,
}

# Game → Steam appid mapping
GAME_APPID = {"cs2": "730", "csgo": "730", "dota2": "570", "tf2": "440", "rust": "252490"}

# Marketplace slug → item page URL template
# {name} = raw name, {q} = URL-encoded name, {app} = Steam appid
ITEM_URL_PATTERNS: dict[str, str] = {
    "steam": "https://steamcommunity.com/market/listings/730/{q}",
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


def get_sell_fee_multiplier(slug: str) -> float:
    """Return (1 - fee%) multiplier for selling on a marketplace."""
    fee_pct = MARKETPLACE_FEES.get(slug, 5.0)
    return 1.0 - (fee_pct / 100.0)


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
    db: AsyncSession, item_id: str
) -> list[ArbitrageOpportunity]:
    """Calculate cross-marketplace arbitrage for an item.

    Compares every pair of marketplaces: buy on one, sell on another.
    Accounts for the sell-side marketplace fee.
    """
    # Deactivate previous opportunities for this item
    await db.execute(
        ArbitrageOpportunity.__table__.update()
        .where(ArbitrageOpportunity.item_id == item_id)
        .values(is_active=False)
    )

    # Get latest price snapshot for each marketplace
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
        .where(PriceSnapshot.item_id == item_id)
    )

    results = (await db.execute(query)).all()

    # Build marketplace price map: {marketplace_id: (price, marketplace)}
    price_map: dict[int, tuple[float, Marketplace]] = {}
    for snapshot, marketplace in results:
        price = float(snapshot.price_usd)
        if price > 0:
            price_map[marketplace.id] = (price, marketplace)

    opportunities = []

    # Compare every pair: buy on A, sell on B
    for buy_mp_id, (buy_price, buy_mp) in price_map.items():
        for sell_mp_id, (sell_price, sell_mp) in price_map.items():
            if buy_mp_id == sell_mp_id:
                continue

            # Apply sell-side fee
            sell_fee_mult = get_sell_fee_multiplier(sell_mp.slug)
            sell_after_fee = sell_price * sell_fee_mult

            profit_usd = sell_after_fee - buy_price
            if buy_price <= 0:
                continue
            profit_pct = ((sell_after_fee / buy_price) - 1) * 100

            if profit_pct >= 0:
                opp = ArbitrageOpportunity(
                    item_id=item_id,
                    buy_marketplace_id=buy_mp_id,
                    sell_marketplace_id=sell_mp_id,
                    buy_price_usd=buy_price,
                    sell_price_usd=sell_price,
                    sell_price_after_fee=round(sell_after_fee, 2),
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
    BuyMP = aliased(Marketplace, name="buy_mp")
    SellMP = aliased(Marketplace, name="sell_mp")

    base_where = [ArbitrageOpportunity.is_active.is_(True)]

    if filters.min_profit_pct > 0:
        base_where.append(ArbitrageOpportunity.profit_pct >= filters.min_profit_pct)
    if filters.max_profit_pct is not None:
        base_where.append(ArbitrageOpportunity.profit_pct <= filters.max_profit_pct)

    query = (
        select(ArbitrageOpportunity, Item, BuyMP, SellMP)
        .join(Item, ArbitrageOpportunity.item_id == Item.id)
        .join(BuyMP, ArbitrageOpportunity.buy_marketplace_id == BuyMP.id)
        .join(SellMP, ArbitrageOpportunity.sell_marketplace_id == SellMP.id)
        .where(*base_where)
    )
    count_query = (
        select(func.count(ArbitrageOpportunity.id))
        .join(Item, ArbitrageOpportunity.item_id == Item.id)
        .join(BuyMP, ArbitrageOpportunity.buy_marketplace_id == BuyMP.id)
        .join(SellMP, ArbitrageOpportunity.sell_marketplace_id == SellMP.id)
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
    if filters.buy_marketplace_slug:
        query = query.where(BuyMP.slug == filters.buy_marketplace_slug)
        count_query = count_query.where(BuyMP.slug == filters.buy_marketplace_slug)
    if filters.sell_marketplace_slug:
        query = query.where(SellMP.slug == filters.sell_marketplace_slug)
        count_query = count_query.where(SellMP.slug == filters.sell_marketplace_slug)
    # Legacy filter: marketplace_slug filters buy side
    if filters.marketplace_slug and not filters.buy_marketplace_slug:
        query = query.where(BuyMP.slug == filters.marketplace_slug)
        count_query = count_query.where(BuyMP.slug == filters.marketplace_slug)
    if filters.search:
        query = query.where(Item.market_hash_name.ilike(f"%{filters.search}%"))
        count_query = count_query.where(Item.market_hash_name.ilike(f"%{filters.search}%"))

    sort_col_map = {
        "profit_pct": ArbitrageOpportunity.profit_pct,
        "profit_usd": ArbitrageOpportunity.profit_usd,
        "buy_price": ArbitrageOpportunity.buy_price_usd,
        "sell_price": ArbitrageOpportunity.sell_price_usd,
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
    for opp, item, buy_marketplace, sell_marketplace in results:
        items.append({
            "id": opp.id,
            "item_id": item.id,
            "market_hash_name": item.market_hash_name,
            "game": item.game,
            "icon_url": item.icon_url,
            "item_type": item.item_type,
            "buy_marketplace_name": buy_marketplace.name,
            "buy_marketplace_slug": buy_marketplace.slug,
            "buy_marketplace_url": build_item_url(
                buy_marketplace.slug, buy_marketplace.base_url, item.market_hash_name
            ),
            "sell_marketplace_name": sell_marketplace.name,
            "sell_marketplace_slug": sell_marketplace.slug,
            "sell_marketplace_url": build_item_url(
                sell_marketplace.slug, sell_marketplace.base_url, item.market_hash_name
            ),
            "buy_marketplace_fee_pct": MARKETPLACE_FEES.get(buy_marketplace.slug, 5.0),
            "sell_marketplace_fee_pct": MARKETPLACE_FEES.get(sell_marketplace.slug, 5.0),
            "buy_price_usd": float(opp.buy_price_usd),
            "sell_price_usd": float(opp.sell_price_usd),
            "sell_price_after_fee": float(opp.sell_price_after_fee),
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
