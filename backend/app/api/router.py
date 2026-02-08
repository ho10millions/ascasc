from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.arbitrage import router as arbitrage_router
from app.api.v1.auth import router as auth_router
from app.api.v1.items import router as items_router
from app.api.v1.marketplaces import router as marketplaces_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(items_router)
api_router.include_router(arbitrage_router)
api_router.include_router(marketplaces_router)
api_router.include_router(admin_router)
