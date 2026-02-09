from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialsException, ForbiddenException
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User


async def get_current_user(
    authorization: str = Header(..., description="Bearer <token>"),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise CredentialsException()

    token = authorization[7:]
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise CredentialsException()

    user_id = payload.get("sub")
    if not user_id:
        raise CredentialsException()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise CredentialsException()

    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise ForbiddenException()
    return user
