import aiosqlite
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from config import config


DB_PATH = config.DB_PATH

PERIODS = {
    "week": {"days": 7, "label": "1 неделя", "price": config.PRICE_WEEK},
    "month": {"days": 30, "label": "1 месяц", "price": config.PRICE_MONTH},
    "3months": {"days": 90, "label": "3 месяца", "price": config.PRICE_3MONTHS},
}


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                first_name  TEXT,
                created_at  TEXT NOT NULL,
                state       TEXT DEFAULT 'new'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                period          TEXT NOT NULL,
                price           INTEGER NOT NULL,
                status          TEXT DEFAULT 'pending',
                payment_proof   TEXT,
                created_at      TEXT NOT NULL,
                expires_at      TEXT,
                approved_at     TEXT,
                approved_by     INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        """)
        await db.commit()


# ── Users ──────────────────────────────────────────────────────────────────────

async def upsert_user(user_id: int, username: Optional[str], first_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, first_name, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name
        """, (user_id, username, first_name, datetime.utcnow().isoformat()))
        await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_user_state(user_id: int, state: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET state = ? WHERE user_id = ?", (state, user_id)
        )
        await db.commit()


# ── Subscriptions ──────────────────────────────────────────────────────────────

async def create_subscription(user_id: int, period: str) -> int:
    price = PERIODS[period]["price"]
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("""
            INSERT INTO subscriptions (user_id, period, price, status, created_at)
            VALUES (?, ?, ?, 'pending', ?)
        """, (user_id, period, price, datetime.utcnow().isoformat()))
        await db.commit()
        return cur.lastrowid


async def set_payment_proof(sub_id: int, file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE subscriptions SET payment_proof = ?, status = 'proof_sent'
            WHERE id = ?
        """, (file_id, sub_id))
        await db.commit()


async def approve_subscription(sub_id: int, admin_id: int):
    """Approve and set expires_at based on period."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT period FROM subscriptions WHERE id = ?", (sub_id,)
        ) as cur:
            row = await cur.fetchone()
        if not row:
            return None
        days = PERIODS[row["period"]]["days"]
        now = datetime.utcnow()
        expires_at = (now + timedelta(days=days)).isoformat()
        await db.execute("""
            UPDATE subscriptions
            SET status = 'active', approved_at = ?, approved_by = ?, expires_at = ?
            WHERE id = ?
        """, (now.isoformat(), admin_id, expires_at, sub_id))
        await db.commit()
        return expires_at


async def reject_subscription(sub_id: int, admin_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE subscriptions SET status = 'rejected', approved_by = ?, approved_at = ?
            WHERE id = ?
        """, (admin_id, datetime.utcnow().isoformat(), sub_id))
        await db.commit()


async def get_active_subscription(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM subscriptions
            WHERE user_id = ? AND status = 'active'
            ORDER BY expires_at DESC LIMIT 1
        """, (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_pending_subscription(user_id: int) -> Optional[dict]:
    """Get latest subscription awaiting proof or approval."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM subscriptions
            WHERE user_id = ? AND status IN ('pending', 'proof_sent')
            ORDER BY id DESC LIMIT 1
        """, (user_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_subscription_by_id(sub_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM subscriptions WHERE id = ?", (sub_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_expired_active_subscriptions() -> list[dict]:
    """Return all subscriptions that are active but have expired."""
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM subscriptions
            WHERE status = 'active' AND expires_at <= ?
        """, (now,)) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def expire_subscription(sub_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE subscriptions SET status = 'expired' WHERE id = ?", (sub_id,)
        )
        await db.commit()
