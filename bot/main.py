import asyncio
import logging
import sys
import os

# Allow imports from bot/ directory
sys.path.insert(0, os.path.dirname(__file__))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import config
from database import init_db
from handlers.user import router as user_router
from handlers.admin import router as admin_router
from scheduler import scheduler_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not set. Please set it in environment variables.")
        sys.exit(1)

    if not config.ADMIN_IDS:
        logger.warning(
            "ADMIN_IDS is not set. "
            "Set ADMIN_IDS=your_telegram_id to receive payment notifications."
        )

    # Init database
    await init_db()
    logger.info("Database initialized.")

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_router(admin_router)  # admin first so admin callbacks take priority
    dp.include_router(user_router)

    # Start background scheduler
    asyncio.create_task(scheduler_loop(bot))

    logger.info("Bot started.")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
