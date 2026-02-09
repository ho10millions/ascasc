from datetime import datetime

from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=6, max_length=100)
    invite_code: str = Field(min_length=1, max_length=30)


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_admin: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenRefresh(BaseModel):
    refresh_token: str


class InviteCodeCreate(BaseModel):
    max_uses: int = Field(default=1, ge=1, le=100)
    grants_admin: bool = False


class InviteCodeResponse(BaseModel):
    id: str
    code: str
    max_uses: int
    times_used: int
    is_active: bool
    grants_admin: bool
    expires_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
