"""
Background task: checks every minute for expired subscriptions
and notifies users + admins.
"""
import asyncio
import logging
from aiogram import Bot

import database as db
from config import config

logger = logging.getLogger(__name__)


async def check_expired(bot: Bot):
    expired_list = await db.get_expired_active_subscriptions()
    for sub in expired_list:
        await db.expire_subscription(sub["id"])
        await db.set_user_state(sub["user_id"], "expired")

        # Notify user
        try:
            await bot.send_message(
                sub["user_id"],
                "⏰ <b>Ваша подписка истекла.</b>\n\n"
                "Доступ к привату закрыт.\n\n"
                "Чтобы продлить — нажмите /start 💋",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify user {sub['user_id']}: {e}")

        # Notify admins
        from database import PERIODS
        period_info = PERIODS.get(sub["period"], {"label": sub["period"]})
        for admin_id in config.ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"🔔 Подписка #{sub['id']} пользователя "
                    f"<code>{sub['user_id']}</code> (<b>{period_info['label']}</b>) истекла.",
                    parse_mode="HTML"
                )
            except Exception:
                pass


async def scheduler_loop(bot: Bot):
    while True:
        try:
            await check_expired(bot)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(60)  # check every minute
