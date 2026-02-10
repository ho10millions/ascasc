import asyncio
import logging
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

logger = logging.getLogger(__name__)

# Global scraper state
scraper_status = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "items_total": 0,
}


# (name, slug, base_url, scraper_type, enabled)
# enabled=True only for marketplaces with verified public APIs
MARKETPLACE_SEEDS = [
    ("Steam Market", "steam", "https://steamcommunity.com/market", "api", True),
    ("Market CSGO", "market-csgo", "https://market.csgo.com", "api", True),
    ("Waxpeer", "waxpeer", "https://waxpeer.com", "api", True),
    ("Loot.Farm", "loot-farm", "https://loot.farm", "api", True),
    ("DMarket", "dmarket", "https://dmarket.com", "api", True),
    ("CSFloat", "csfloat", "https://csfloat.com", "api", True),
    ("CS.Money", "cs-money", "https://cs.money", "api", True),
    ("ShadowPay", "shadowpay", "https://shadowpay.com", "api", True),
    ("Buff163", "buff163", "https://buff.163.com", "api", True),
    ("Buff Market", "buff-market", "https://buff.market", "api", True),
    ("Swap.gg", "swap-gg", "https://swap.gg", "api", True),
    ("Youpin898", "youpin898", "https://youpin898.com", "api", True),
    ("RapidSkins", "rapidskins", "https://rapidskins.com", "api", True),
    # Below: no verified public API — disabled by default (enable in Admin if needed)
    ("SkinSwap", "skinswap", "https://skinswap.com", "api", False),
    ("Skins.Cash", "skins-cash", "https://skins.cash", "api", False),
    ("White Market", "white-market", "https://white.market", "api", False),
    ("Lis-Skins", "lis-skins", "https://lis-skins.com", "api", False),
    ("Skinomat", "skinomat", "https://skinomat.com", "api", False),
    ("Aim Market", "aim-market", "https://aim.market", "api", False),
    ("Avan Market", "avan-market", "https://avan.market", "api", False),
    ("PirateSwap", "pirateswap", "https://pirateswap.com", "api", False),
    ("Moon Market", "moon-market", "https://moon.market", "api", False),
    ("Skin.Place", "skin-place", "https://skin.place", "api", False),
    ("Skin.Land", "skin-land", "https://skin.land", "api", False),
    ("iTrade.gg", "itrade-gg", "https://itrade.gg", "api", False),
    ("Skins.com", "skins-com", "https://skins.com", "api", False),
    ("SkinCashier", "skincashier", "https://skincashier.com", "api", False),
    ("CS.Trade", "cs-trade", "https://cs.trade", "api", False),
    ("SkinCantor", "skincantor", "https://skincantor.com", "api", False),
    ("Skinout.gg", "skinout-gg", "https://skinout.gg", "api", False),
]


async def seed_data():
    async with async_session_maker() as session:
        for name, slug, url, scraper_type, enabled in MARKETPLACE_SEEDS:
            existing = await session.execute(
                select(Marketplace).where(Marketplace.slug == slug)
            )
            mkt = existing.scalar_one_or_none()
            if mkt:
                # Update enabled status for existing marketplaces
                mkt.is_enabled = enabled
            else:
                session.add(Marketplace(
                    name=name, slug=slug, base_url=url,
                    scraper_type=scraper_type, is_enabled=enabled,
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


async def background_scraper():
    """Background task that runs scrape cycles periodically."""
    from app.scrapers.scheduler import run_full_scrape_cycle
    from datetime import datetime, timezone

    await asyncio.sleep(10)  # Wait for server to fully start
    interval = settings.SCRAPE_INTERVAL_MINUTES * 60

    while True:
        if not scraper_status["running"]:
            scraper_status["running"] = True
            try:
                logger.info("Background scraper: starting cycle...")
                await run_full_scrape_cycle()
                scraper_status["last_run"] = datetime.now(timezone.utc).isoformat()
                scraper_status["last_result"] = "success"
                logger.info("Background scraper: cycle complete")
            except Exception as e:
                logger.error(f"Background scraper failed: {e}")
                scraper_status["last_result"] = f"error: {str(e)[:200]}"
            finally:
                scraper_status["running"] = False

        logger.info(f"Next scrape in {settings.SCRAPE_INTERVAL_MINUTES} minutes...")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()

    # Start background scraper
    task = asyncio.create_task(background_scraper())
    logger.info("Background scraper task started")

    yield

    task.cancel()
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


@app.get("/api/v1/scraper-status")
async def get_scraper_status():
    return scraper_status


# ---------- Embedded HTML Frontend ----------

_frontend_path = os.path.join(os.path.dirname(__file__), "frontend.html")
FRONTEND_HTML = ""
if os.path.exists(_frontend_path):
    with open(_frontend_path, "r", encoding="utf-8") as f:
        FRONTEND_HTML = f.read()
else:
    FRONTEND_HTML = "<h1>Frontend not found</h1>"


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    return FRONTEND_HTML


@app.get("/{path:path}", response_class=HTMLResponse)
async def serve_frontend_catchall(path: str):
    if path.startswith("api/") or path == "health" or path == "docs" or path == "openapi.json" or path == "redoc":
        return None
    return FRONTEND_HTML
