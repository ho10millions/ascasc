import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.arbitrage import ArbitrageFilters, ArbitrageResponse
from app.schemas.pagination import PaginatedResponse
from app.services.arbitrage_service import get_arbitrage_opportunities, get_arbitrage_stats

router = APIRouter(prefix="/arbitrage", tags=["arbitrage"])


@router.get("", response_model=PaginatedResponse[ArbitrageResponse])
async def list_arbitrage(
    min_profit_pct: float = Query(0, ge=0),
    max_profit_pct: float | None = None,
    game: str | None = None,
    item_type: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    marketplace_slug: str | None = None,
    buy_marketplace_slug: str | None = None,
    sell_marketplace_slug: str | None = None,
    search: str | None = None,
    sort_by: str = "profit_pct",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    filters = ArbitrageFilters(
        min_profit_pct=min_profit_pct,
        max_profit_pct=max_profit_pct,
        game=game,
        item_type=item_type,
        min_price=min_price,
        max_price=max_price,
        marketplace_slug=marketplace_slug,
        buy_marketplace_slug=buy_marketplace_slug,
        sell_marketplace_slug=sell_marketplace_slug,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )

    items, total = await get_arbitrage_opportunities(db, filters)
    return PaginatedResponse(
        items=[ArbitrageResponse(**item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/stats")
async def arbitrage_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await get_arbitrage_stats(db)
