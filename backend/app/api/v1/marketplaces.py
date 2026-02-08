from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.marketplace import Marketplace
from app.models.user import User
from app.schemas.marketplace import MarketplaceResponse

router = APIRouter(prefix="/marketplaces", tags=["marketplaces"])


@router.get("", response_model=list[MarketplaceResponse])
async def list_marketplaces(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(Marketplace).order_by(Marketplace.name))
    marketplaces = result.scalars().all()
    return [MarketplaceResponse.model_validate(m) for m in marketplaces]
