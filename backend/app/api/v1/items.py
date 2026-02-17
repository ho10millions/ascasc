import math

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.schemas.item import ItemResponse
from app.schemas.pagination import PaginatedResponse
from app.schemas.price import ItemPriceComparison, PriceComparisonEntry
from app.services.item_service import get_item_by_id, get_item_prices, get_items

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=PaginatedResponse[ItemResponse])
async def list_items(
    game: str | None = None,
    item_type: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    items, total = await get_items(db, game=game, item_type=item_type, search=search, page=page, per_page=per_page)
    return PaginatedResponse(
        items=[ItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    item = await get_item_by_id(db, item_id)
    if not item:
        raise NotFoundException("Item not found")
    return ItemResponse.model_validate(item)


@router.get("/{item_id}/prices", response_model=ItemPriceComparison)
async def get_item_price_comparison(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    item = await get_item_by_id(db, item_id)
    if not item:
        raise NotFoundException("Item not found")

    prices = await get_item_prices(db, item_id)

    steam_price = None
    steam_after_fee = None
    price_entries = []

    for p in prices:
        if p["marketplace_slug"] == "steam":
            steam_price = p["price_usd"]
            steam_after_fee = round(steam_price * 0.87, 2)
        price_entries.append(PriceComparisonEntry(**p))

    return ItemPriceComparison(
        item_id=item.id,
        market_hash_name=item.market_hash_name,
        game=item.game,
        steam_price=steam_price,
        steam_price_after_fee=steam_after_fee,
        prices=price_entries,
    )
