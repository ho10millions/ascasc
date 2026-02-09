import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, CredentialsException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import InviteCode, User
from app.schemas.user import TokenResponse, UserRegister, UserResponse


async def register_user(db: AsyncSession, data: UserRegister) -> TokenResponse:
    result = await db.execute(
        select(InviteCode).where(InviteCode.code == data.invite_code, InviteCode.is_active.is_(True))
    )
    invite = result.scalar_one_or_none()

    if not invite:
        raise BadRequestException("Invalid or expired invite code")
    if invite.times_used >= invite.max_uses:
        raise BadRequestException("Invite code has been fully used")
    if invite.expires_at and invite.expires_at < datetime.now(timezone.utc):
        raise BadRequestException("Invite code has expired")

    existing = await db.execute(
        select(User).where((User.username == data.username) | (User.email == data.email))
    )
    if existing.scalar_one_or_none():
        raise BadRequestException("Username or email already taken")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        is_admin=invite.grants_admin,
        invited_by_code_id=invite.id,
    )
    db.add(user)

    invite.times_used += 1
    if invite.times_used >= invite.max_uses:
        invite.is_active = False

    await db.flush()

    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def login_user(db: AsyncSession, username: str, password: str) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise CredentialsException()

    if not user.is_active:
        raise BadRequestException("Account is deactivated")

    token_data = {"sub": str(user.id), "username": user.username}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise CredentialsException()

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise CredentialsException()

    token_data = {"sub": str(user.id), "username": user.username}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        user=UserResponse.model_validate(user),
    )


async def generate_invite_code(
    db: AsyncSession, created_by: str, max_uses: int = 1, grants_admin: bool = False
) -> InviteCode:
    code = f"SCR-{secrets.token_urlsafe(8).upper()}"
    invite = InviteCode(
        code=code,
        created_by_user_id=created_by,
        max_uses=max_uses,
        grants_admin=grants_admin,
    )
    db.add(invite)
    await db.flush()
    return invite
