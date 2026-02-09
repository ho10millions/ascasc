from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.marketplace import Marketplace
from app.models.scrape_job import ScrapeJob
from app.models.user import InviteCode, User


async def get_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def toggle_user_active(db: AsyncSession, user_id: str, is_active: bool) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_active = is_active
        await db.flush()
    return user


async def get_all_invite_codes(db: AsyncSession) -> list[InviteCode]:
    result = await db.execute(select(InviteCode).order_by(InviteCode.created_at.desc()))
    return list(result.scalars().all())


async def deactivate_invite_code(db: AsyncSession, code_id: str) -> InviteCode | None:
    result = await db.execute(select(InviteCode).where(InviteCode.id == code_id))
    code = result.scalar_one_or_none()
    if code:
        code.is_active = False
        await db.flush()
    return code


async def get_scrape_jobs(
    db: AsyncSession, marketplace_id: int | None = None, limit: int = 50
) -> list[ScrapeJob]:
    query = select(ScrapeJob).order_by(ScrapeJob.created_at.desc()).limit(limit)
    if marketplace_id:
        query = query.where(ScrapeJob.marketplace_id == marketplace_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_marketplace(
    db: AsyncSession, marketplace_id: int, is_enabled: bool | None = None,
    scrape_interval: int | None = None,
) -> Marketplace | None:
    result = await db.execute(select(Marketplace).where(Marketplace.id == marketplace_id))
    mkt = result.scalar_one_or_none()
    if mkt:
        if is_enabled is not None:
            mkt.is_enabled = is_enabled
        if scrape_interval is not None:
            mkt.scrape_interval_minutes = scrape_interval
        await db.flush()
    return mkt
