import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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


# ==================== WebSocket Manager ====================
class WSManager:
    """Manages WebSocket connections and broadcasts."""
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, msg: dict):
        dead = []
        for ws in self.connections:
            try:
                await ws.send_json(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self.connections:
                self.connections.remove(ws)


ws_manager = WSManager()


# ==================== Scraper Status ====================
scraper_status = {
    "running": False,
    "last_run": None,
    "last_result": None,
    "items_total": 0,
    "current_marketplace": None,
    "progress": [],
}


# ==================== Marketplace Seeds ====================
# (name, slug, base_url, scraper_type, enabled)
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
    # No verified public API — disabled by default
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


# ==================== Background Scraper ====================
async def on_scraper_progress(slug: str, count: int):
    """Called during scrape cycle to broadcast live progress via WebSocket."""
    scraper_status["current_marketplace"] = slug
    scraper_status["progress"].append({"slug": slug, "items": count})
    await ws_manager.broadcast({
        "type": "scraper_progress",
        "marketplace": slug,
        "items_saved": count,
        "total_so_far": sum(p["items"] for p in scraper_status["progress"]),
    })


async def background_scraper():
    """Background task that runs scrape cycles periodically."""
    from app.scrapers.scheduler import run_full_scrape_cycle
    from datetime import datetime, timezone

    await asyncio.sleep(10)
    interval = settings.SCRAPE_INTERVAL_MINUTES * 60

    while True:
        if not scraper_status["running"]:
            scraper_status["running"] = True
            scraper_status["progress"] = []
            scraper_status["current_marketplace"] = None
            await ws_manager.broadcast({"type": "scraper_status", "running": True})
            try:
                logger.info("Background scraper: starting cycle...")
                total = await run_full_scrape_cycle(on_progress=on_scraper_progress)
                scraper_status["last_run"] = datetime.now(timezone.utc).isoformat()
                scraper_status["last_result"] = "success"
                scraper_status["items_total"] = total
                logger.info("Background scraper: cycle complete")
            except Exception as e:
                logger.error(f"Background scraper failed: {e}")
                scraper_status["last_result"] = f"error: {str(e)[:200]}"
            finally:
                scraper_status["running"] = False
                scraper_status["current_marketplace"] = None
                await ws_manager.broadcast({
                    "type": "scraper_status",
                    "running": False,
                    "last_run": scraper_status["last_run"],
                    "last_result": scraper_status["last_result"],
                    "items_total": scraper_status["items_total"],
                })
                # Tell clients to refresh data
                await ws_manager.broadcast({"type": "data_updated"})

        logger.info(f"Next scrape in {settings.SCRAPE_INTERVAL_MINUTES} minutes...")
        await asyncio.sleep(interval)


# ==================== App Lifecycle ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_data()

    task = asyncio.create_task(background_scraper())
    logger.info("Background scraper task started")

    yield

    task.cancel()
    await engine.dispose()


app = FastAPI(
    title="Scrooge's Price Aggregator",
    description="Gaming item price aggregator and arbitrage hunter",
    version="2.0.0",
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


# ==================== WebSocket Endpoint ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    # Send current status immediately on connect
    try:
        await websocket.send_json({
            "type": "scraper_status",
            "running": scraper_status["running"],
            "last_run": scraper_status["last_run"],
            "last_result": scraper_status["last_result"],
            "items_total": scraper_status["items_total"],
        })
    except Exception:
        pass
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ==================== Price History API ====================
@app.get("/api/v1/items/{item_id}/price-history")
async def get_price_history_endpoint(
    item_id: str,
    days: int = 7,
):
    from datetime import timedelta
    from sqlalchemy import select, and_
    from app.models.price import PriceSnapshot
    from app.models.marketplace import Marketplace
    from datetime import datetime, timezone

    since = datetime.now(timezone.utc) - timedelta(days=days)

    async with async_session_maker() as db:
        query = (
            select(PriceSnapshot, Marketplace)
            .join(Marketplace, PriceSnapshot.marketplace_id == Marketplace.id)
            .where(
                PriceSnapshot.item_id == item_id,
                PriceSnapshot.scraped_at >= since,
            )
            .order_by(PriceSnapshot.scraped_at.asc())
        )
        results = (await db.execute(query)).all()

    history = []
    for snap, mkt in results:
        history.append({
            "marketplace": mkt.name,
            "marketplace_slug": mkt.slug,
            "price_usd": float(snap.price_usd),
            "scraped_at": snap.scraped_at.isoformat(),
        })
    return {"item_id": item_id, "history": history}


# ==================== Favorites API ====================
@app.get("/api/v1/favorites")
async def get_favorites(user_id: str = None):
    """Get user's favorite items. Uses query param for simplicity."""
    from app.models.item import Item
    if not user_id:
        return {"favorites": []}
    async with async_session_maker() as db:
        from app.models.favorite import Favorite
        result = await db.execute(
            select(Favorite, Item)
            .join(Item, Favorite.item_id == Item.id)
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.created_at.desc())
        )
        favs = []
        for fav, item in result.all():
            favs.append({
                "id": fav.id,
                "item_id": item.id,
                "market_hash_name": item.market_hash_name,
                "game": item.game,
                "icon_url": item.icon_url,
                "item_type": item.item_type,
                "added_at": fav.created_at.isoformat() if fav.created_at else None,
            })
    return {"favorites": favs}


@app.post("/api/v1/favorites")
async def add_favorite(body: dict):
    from app.models.favorite import Favorite
    user_id = body.get("user_id")
    item_id = body.get("item_id")
    if not user_id or not item_id:
        return {"error": "user_id and item_id required"}
    async with async_session_maker() as db:
        existing = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.item_id == item_id
            )
        )
        if existing.scalar_one_or_none():
            return {"status": "already_exists"}
        db.add(Favorite(user_id=user_id, item_id=item_id))
        await db.commit()
    return {"status": "added"}


@app.delete("/api/v1/favorites/{item_id}")
async def remove_favorite(item_id: str, user_id: str = ""):
    from app.models.favorite import Favorite
    if not user_id:
        return {"error": "user_id required"}
    async with async_session_maker() as db:
        result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.item_id == item_id
            )
        )
        fav = result.scalar_one_or_none()
        if fav:
            await db.delete(fav)
            await db.commit()
    return {"status": "removed"}


# ==================== Embedded Frontend ====================
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
    if path.startswith("api/") or path in ("health", "docs", "openapi.json", "redoc", "ws"):
        return None
    return FRONTEND_HTML
