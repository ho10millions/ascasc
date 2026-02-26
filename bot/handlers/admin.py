from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import database as db
from config import config
from database import PERIODS

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


# ── Guard: only admins pass through ───────────────────────────────────────────

@router.callback_query(F.data.startswith("approve:"))
async def cb_approve(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    _, sub_id_str, user_id_str = call.data.split(":")
    sub_id = int(sub_id_str)
    user_id = int(user_id_str)

    sub = await db.get_subscription_by_id(sub_id)
    if not sub:
        await call.answer("Подписка не найдена", show_alert=True)
        return
    if sub["status"] == "active":
        await call.answer("Уже одобрено", show_alert=True)
        return
    if sub["status"] == "rejected":
        await call.answer("Подписка уже отклонена", show_alert=True)
        return

    expires_at = await db.approve_subscription(sub_id, call.from_user.id)
    await db.set_user_state(user_id, "active")

    expires_dt = datetime.fromisoformat(expires_at)
    expires_str = expires_dt.strftime("%d.%m.%Y %H:%M")
    period_info = PERIODS[sub["period"]]

    # Notify admin
    await call.message.edit_caption(
        call.message.caption + f"\n\n✅ <b>ОДОБРЕНО</b> — доступ до {expires_str}",
        parse_mode="HTML"
    )
    await call.answer("Одобрено!")

    # Notify user
    try:
        await bot.send_message(
            user_id,
            f"🎉 <b>Оплата подтверждена!</b>\n\n"
            f"Твоя подписка на <b>{period_info['label']}</b> активирована 🔥\n"
            f"Доступ действует до: <b>{expires_str}</b>\n\n"
            f"Добро пожаловать в приват! 💋",
            parse_mode="HTML"
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("reject:"))
async def cb_reject(call: CallbackQuery, bot: Bot):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return

    _, sub_id_str, user_id_str = call.data.split(":")
    sub_id = int(sub_id_str)
    user_id = int(user_id_str)

    sub = await db.get_subscription_by_id(sub_id)
    if not sub:
        await call.answer("Подписка не найдена", show_alert=True)
        return
    if sub["status"] in ("active", "rejected"):
        await call.answer(f"Статус: {sub['status']}", show_alert=True)
        return

    await db.reject_subscription(sub_id, call.from_user.id)
    await db.set_user_state(user_id, "rejected")

    # Notify admin
    await call.message.edit_caption(
        call.message.caption + "\n\n❌ <b>ОТКЛОНЕНО</b>",
        parse_mode="HTML"
    )
    await call.answer("Отклонено")

    # Notify user
    try:
        await bot.send_message(
            user_id,
            "❌ <b>Оплата не подтверждена.</b>\n\n"
            "К сожалению, ваш платёж не прошёл проверку.\n"
            "Если вы считаете это ошибкой — свяжитесь с поддержкой.\n\n"
            "Вы можете попробовать снова: /start",
            parse_mode="HTML"
        )
    except Exception:
        pass


# ── Admin stats command ────────────────────────────────────────────────────────

@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    if not is_admin(msg.from_user.id):
        return

    import aiosqlite
    async with aiosqlite.connect(config.DB_PATH) as database:
        database.row_factory = aiosqlite.Row

        async with database.execute("SELECT COUNT(*) as cnt FROM users") as cur:
            total_users = (await cur.fetchone())["cnt"]

        async with database.execute(
            "SELECT COUNT(*) as cnt FROM subscriptions WHERE status = 'active'"
        ) as cur:
            active_subs = (await cur.fetchone())["cnt"]

        async with database.execute(
            "SELECT COUNT(*) as cnt FROM subscriptions WHERE status = 'proof_sent'"
        ) as cur:
            pending_subs = (await cur.fetchone())["cnt"]

        async with database.execute(
            "SELECT SUM(price) as total FROM subscriptions WHERE status IN ('active','expired')"
        ) as cur:
            row = await cur.fetchone()
            total_revenue = row["total"] or 0

    await msg.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{total_users}</b>\n"
        f"✅ Активных подписок: <b>{active_subs}</b>\n"
        f"⏳ Ожидают проверки: <b>{pending_subs}</b>\n"
        f"💰 Общий доход: <b>{total_revenue} ₽</b>",
        parse_mode="HTML"
    )


@router.message(Command("pending"))
async def cmd_pending(msg: Message, bot: Bot):
    """List all pending proof_sent subscriptions."""
    if not is_admin(msg.from_user.id):
        return

    import aiosqlite
    async with aiosqlite.connect(config.DB_PATH) as database:
        database.row_factory = aiosqlite.Row
        async with database.execute("""
            SELECT s.*, u.username, u.first_name
            FROM subscriptions s
            JOIN users u ON u.user_id = s.user_id
            WHERE s.status = 'proof_sent'
            ORDER BY s.id DESC
        """) as cur:
            rows = [dict(r) for r in await cur.fetchall()]

    if not rows:
        await msg.answer("Нет ожидающих проверки платежей.")
        return

    from keyboards import kb_admin_approve
    for sub in rows:
        period_info = PERIODS[sub["period"]]
        username_str = f"@{sub['username']}" if sub["username"] else "нет username"
        user_link = f'<a href="tg://user?id={sub["user_id"]}">{sub["first_name"]}</a>'
        caption = (
            f"💰 <b>Ожидает проверки</b>\n\n"
            f"👤 Пользователь: {user_link} ({username_str})\n"
            f"🆔 ID: <code>{sub['user_id']}</code>\n"
            f"📦 Период: <b>{period_info['label']}</b>\n"
            f"💵 Сумма: <b>{sub['price']} ₽</b>\n"
            f"🔖 Подписка №{sub['id']}"
        )
        try:
            if sub["payment_proof"]:
                await bot.send_photo(
                    msg.from_user.id,
                    photo=sub["payment_proof"],
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb_admin_approve(sub["id"], sub["user_id"])
                )
        except Exception:
            await msg.answer(caption, parse_mode="HTML",
                             reply_markup=kb_admin_approve(sub["id"], sub["user_id"]))
