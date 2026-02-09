import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.exceptions import NotFoundException
from app.db.session import get_db
from app.models.user import User
from app.schemas.marketplace import MarketplaceResponse, MarketplaceUpdate
from app.schemas.user import InviteCodeCreate, InviteCodeResponse, UserResponse
from app.services.admin_service import (
    deactivate_invite_code,
    get_all_invite_codes,
    get_all_users,
    get_scrape_jobs,
    toggle_user_active,
    update_marketplace,
)
from app.services.auth_service import generate_invite_code

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    users = await get_all_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.patch("/users/{user_id}/toggle")
async def toggle_user(
    user_id: str,
    is_active: bool,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    user = await toggle_user_active(db, user_id, is_active)
    if not user:
        raise NotFoundException("User not found")
    return {"status": "ok", "is_active": user.is_active}


@router.get("/invite-codes", response_model=list[InviteCodeResponse])
async def list_invite_codes(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    codes = await get_all_invite_codes(db)
    return [InviteCodeResponse.model_validate(c) for c in codes]


@router.post("/invite-codes", response_model=InviteCodeResponse)
async def create_invite_code(
    data: InviteCodeCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    code = await generate_invite_code(
        db, created_by=admin.id, max_uses=data.max_uses, grants_admin=data.grants_admin
    )
    return InviteCodeResponse.model_validate(code)


@router.delete("/invite-codes/{code_id}")
async def delete_invite_code(
    code_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    code = await deactivate_invite_code(db, code_id)
    if not code:
        raise NotFoundException("Invite code not found")
    return {"status": "deactivated"}


@router.patch("/marketplaces/{marketplace_id}", response_model=MarketplaceResponse)
async def update_marketplace_settings(
    marketplace_id: int,
    data: MarketplaceUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    mkt = await update_marketplace(
        db, marketplace_id, is_enabled=data.is_enabled, scrape_interval=data.scrape_interval_minutes
    )
    if not mkt:
        raise NotFoundException("Marketplace not found")
    return MarketplaceResponse.model_validate(mkt)


@router.get("/scrape-jobs")
async def list_scrape_jobs(
    marketplace_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    jobs = await get_scrape_jobs(db, marketplace_id=marketplace_id, limit=limit)
    return [
        {
            "id": str(j.id),
            "marketplace_id": j.marketplace_id,
            "status": j.status,
            "items_scraped": j.items_scraped,
            "errors": j.errors,
            "triggered_by": j.triggered_by,
            "started_at": j.started_at,
            "finished_at": j.finished_at,
            "created_at": j.created_at,
        }
        for j in jobs
    ]


@router.post("/scrape-now")
async def trigger_scrape(
    _admin: User = Depends(require_admin),
):
    """Manually trigger a full scrape cycle."""
    from app.main import scraper_status

    if scraper_status["running"]:
        return {"status": "already_running", "message": "Scraper is already running"}

    async def _run_scrape():
        from app.scrapers.scheduler import run_full_scrape_cycle
        from datetime import datetime, timezone

        scraper_status["running"] = True
        try:
            await run_full_scrape_cycle()
            scraper_status["last_run"] = datetime.now(timezone.utc).isoformat()
            scraper_status["last_result"] = "success"
        except Exception as e:
            scraper_status["last_result"] = f"error: {str(e)[:200]}"
        finally:
            scraper_status["running"] = False

    asyncio.create_task(_run_scrape())
    return {"status": "started", "message": "Scrape cycle started in background"}
