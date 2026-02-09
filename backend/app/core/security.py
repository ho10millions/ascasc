import hashlib
import hmac
import json
import base64
import time
from datetime import datetime, timedelta, timezone

from app.config import settings


def hash_password(password: str) -> str:
    salt = hashlib.sha256(settings.SECRET_KEY.encode()).hexdigest()[:16]
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex() + ":" + salt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if ":" not in hashed_password:
        return False
    stored_hash, salt = hashed_password.rsplit(":", 1)
    new_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), 100000).hex()
    return hmac.compare_digest(stored_hash, new_hash)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(header_payload: str) -> str:
    sig = hmac.new(settings.SECRET_KEY.encode(), header_payload.encode(), hashlib.sha256).digest()
    return _b64encode(sig)


def _create_token(data: dict) -> str:
    header = _b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64encode(json.dumps(data, default=str).encode())
    header_payload = f"{header}.{payload}"
    signature = _sign(header_payload)
    return f"{header_payload}.{signature}"


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = int(expire.timestamp())
    to_encode["type"] = "access"
    return _create_token(to_encode)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode["exp"] = int(expire.timestamp())
    to_encode["type"] = "refresh"
    return _create_token(to_encode)


def decode_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_payload = f"{parts[0]}.{parts[1]}"
        expected_sig = _sign(header_payload)
        if not hmac.compare_digest(parts[2], expected_sig):
            return None
        payload_json = _b64decode(parts[1])
        payload = json.loads(payload_json)
        if payload.get("exp") and int(payload["exp"]) < time.time():
            return None
        return payload
    except Exception:
        return None
