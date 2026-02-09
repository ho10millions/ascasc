import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.api.router import api_router
from app.config import settings
from app.db.base import Base
from app.db.session import engine, async_session_maker
from app.models.marketplace import Marketplace
from app.models.user import InviteCode


MARKETPLACE_SEEDS = [
    ("Steam Market", "steam", "https://steamcommunity.com/market", "api"),
    ("SkinSwap", "skinswap", "https://skinswap.com", "api"),
    ("ShadowPay", "shadowpay", "https://shadowpay.com", "api"),
    ("Skins.Cash", "skins-cash", "https://skins.cash", "playwright"),
    ("White Market", "white-market", "https://white.market", "api"),
    ("Waxpeer", "waxpeer", "https://waxpeer.com", "api"),
    ("Lis-Skins", "lis-skins", "https://lis-skins.com", "api"),
    ("Skinomat", "skinomat", "https://skinomat.com", "playwright"),
    ("Aim Market", "aim-market", "https://aim.market", "playwright"),
    ("Avan Market", "avan-market", "https://avan.market", "playwright"),
    ("PirateSwap", "pirateswap", "https://pirateswap.com", "playwright"),
    ("Moon Market", "moon-market", "https://moon.market", "playwright"),
    ("Skin.Place", "skin-place", "https://skin.place", "playwright"),
    ("CS.Money", "cs-money", "https://cs.money", "api"),
    ("Skin.Land", "skin-land", "https://skin.land", "api"),
    ("CSFloat", "csfloat", "https://csfloat.com", "api"),
    ("iTrade.gg", "itrade-gg", "https://itrade.gg", "api"),
    ("DMarket", "dmarket", "https://dmarket.com", "api"),
    ("Skins.com", "skins-com", "https://skins.com", "api"),
    ("SkinCashier", "skincashier", "https://skincashier.com", "playwright"),
    ("Swap.gg", "swap-gg", "https://swap.gg", "api"),
    ("Buff Market", "buff-market", "https://buff.market", "api"),
    ("Market CSGO", "market-csgo", "https://market.csgo.com", "api"),
    ("Buff163", "buff163", "https://buff.163.com", "api"),
    ("CS.Trade", "cs-trade", "https://cs.trade", "api"),
    ("Loot.Farm", "loot-farm", "https://loot.farm", "api"),
    ("SkinCantor", "skincantor", "https://skincantor.com", "playwright"),
    ("Skinout.gg", "skinout-gg", "https://skinout.gg", "playwright"),
    ("Youpin898", "youpin898", "https://youpin898.com", "api"),
    ("RapidSkins", "rapidskins", "https://rapidskins.com", "api"),
]


async def seed_data():
    async with async_session_maker() as session:
        for name, slug, url, scraper_type in MARKETPLACE_SEEDS:
            existing = await session.execute(
                select(Marketplace).where(Marketplace.slug == slug)
            )
            if not existing.scalar_one_or_none():
                session.add(Marketplace(
                    name=name, slug=slug, base_url=url, scraper_type=scraper_type
                ))

        existing_code = await session.execute(
            select(InviteCode).where(InviteCode.code == settings.ADMIN_INVITE_CODE)
        )
        if not existing_code.scalar_one_or_none():
            session.add(InviteCode(
                code=settings.ADMIN_INVITE_CODE,
                max_uses=1,
                grants_admin=True,
            ))

        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()
    yield
    await engine.dispose()


app = FastAPI(
    title="Scrooge's Price Aggregator",
    description="Gaming item price aggregator and arbitrage hunter",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "scrooge-aggregator"}


# ---------- Embedded HTML Frontend ----------

FRONTEND_HTML = open(
    os.path.join(os.path.dirname(__file__), "frontend.html"), "r", encoding="utf-8"
).read() if os.path.exists(os.path.join(os.path.dirname(__file__), "frontend.html")) else "<h1>Frontend not found</h1>"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return FRONTEND_HTML


@app.get("/{path:path}", response_class=HTMLResponse)
async def serve_frontend_catchall(path: str):
    if path.startswith("api/") or path == "health" or path == "docs" or path == "openapi.json" or path == "redoc":
        return None
    return FRONTEND_HTML
