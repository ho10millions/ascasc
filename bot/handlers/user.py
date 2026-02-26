from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, ContentType

import database as db
from config import config
from database import PERIODS
from keyboards import kb_choose_period, kb_paid, kb_change_period

router = Router()


# ── /start ─────────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(msg: Message):
    user = msg.from_user
    await db.upsert_user(user.id, user.username, user.first_name)

    # If user already has an active subscription
    active = await db.get_active_subscription(user.id)
    if active:
        expires = datetime.fromisoformat(active["expires_at"])
        expires_str = expires.strftime("%d.%m.%Y %H:%M")
        await msg.answer(
            f"💎 <b>Добро пожаловать обратно, {user.first_name}!</b>\n\n"
            f"У вас активная подписка до <b>{expires_str}</b>.\n\n"
            f"Наслаждайтесь приватом! 🔥",
            parse_mode="HTML"
        )
        return

    # Check if there's a pending payment
    pending = await db.get_pending_subscription(user.id)
    if pending:
        if pending["status"] == "pending":
            # Resend payment details
            period_info = PERIODS[pending["period"]]
            await msg.answer(
                f"⏳ У вас есть незавершённая оплата.\n\n"
                f"📦 Период: <b>{period_info['label']}</b>\n"
                f"💰 Сумма: <b>{pending['price']} ₽</b>\n\n"
                + _payment_text(pending["id"]),
                parse_mode="HTML",
                reply_markup=kb_paid(pending["id"])
            )
        elif pending["status"] == "proof_sent":
            await msg.answer(
                "⏳ Ваш чек получен и ожидает проверки.\n\n"
                "Как только модель подтвердит оплату — вы получите доступ! 🔥",
                parse_mode="HTML"
            )
        return

    await _send_welcome(msg, user.first_name)


async def _send_welcome(msg: Message, name: str):
    await msg.answer(
        f"👋 <b>Привет, {name}!</b>\n\n"
        f"Добро пожаловать в приват-канал 💋\n\n"
        f"Здесь тебя ждёт эксклюзивный контент, которого нет больше нигде 🔥\n\n"
        f"Выбери период подписки:",
        parse_mode="HTML",
        reply_markup=kb_choose_period()
    )


# ── Period selection ────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("period:"))
async def cb_choose_period(call: CallbackQuery):
    period_key = call.data.split(":")[1]
    if period_key not in PERIODS:
        await call.answer("Неверный период", show_alert=True)
        return

    user = call.from_user
    await db.upsert_user(user.id, user.username, user.first_name)

    # Cancel any old pending sub
    old_pending = await db.get_pending_subscription(user.id)

    # Create new subscription record
    sub_id = await db.create_subscription(user.id, period_key)

    period_info = PERIODS[period_key]
    await call.message.edit_text(
        f"✅ Вы выбрали: <b>{period_info['label']}</b>\n"
        f"💰 Сумма: <b>{period_info['price']} ₽</b>\n\n"
        + _payment_text(sub_id),
        parse_mode="HTML",
        reply_markup=kb_paid(sub_id)
    )
    await call.answer()


def _payment_text(sub_id: int) -> str:
    return (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 <b>Реквизиты для оплаты:</b>\n\n"
        f"🏦 Банк: <b>{config.PAYMENT_BANK}</b>\n"
        f"💳 Карта: <code>{config.PAYMENT_CARD}</code>\n"
        f"👤 Получатель: <b>{config.PAYMENT_HOLDER}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"После оплаты нажми кнопку <b>«Я оплатил(а)»</b> ⬇️"
    )


# ── "I paid" button ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("paid:"))
async def cb_paid(call: CallbackQuery):
    sub_id = int(call.data.split(":")[1])
    sub = await db.get_subscription_by_id(sub_id)

    if not sub or sub["user_id"] != call.from_user.id:
        await call.answer("Подписка не найдена", show_alert=True)
        return

    if sub["status"] not in ("pending", "proof_sent"):
        await call.answer("Эта подписка уже обработана", show_alert=True)
        return

    await db.set_user_state(call.from_user.id, f"awaiting_proof:{sub_id}")

    await call.message.edit_text(
        "📎 <b>Отлично!</b>\n\n"
        "Пожалуйста, пришли скриншот или фото чека об оплате.\n\n"
        "Это ускорит проверку ✅",
        parse_mode="HTML"
    )
    await call.answer()


# ── Receive payment proof ───────────────────────────────────────────────────────

@router.message(F.content_type.in_({ContentType.PHOTO, ContentType.DOCUMENT}))
async def receive_proof(msg: Message, bot: Bot):
    user = await db.get_user(msg.from_user.id)
    if not user:
        return

    state = user.get("state", "")
    if not state.startswith("awaiting_proof:"):
        return

    sub_id = int(state.split(":")[1])
    sub = await db.get_subscription_by_id(sub_id)

    if not sub or sub["user_id"] != msg.from_user.id:
        return

    # Get file_id from photo or document
    if msg.photo:
        file_id = msg.photo[-1].file_id
    else:
        file_id = msg.document.file_id

    await db.set_payment_proof(sub_id, file_id)
    await db.set_user_state(msg.from_user.id, "proof_sent")

    await msg.answer(
        "⏳ <b>Чек получен!</b>\n\n"
        "Ожидай подтверждения от модели.\n"
        "Как только оплата будет проверена — ты получишь доступ к привату! 🔥\n\n"
        "Обычно это занимает до <b>24 часов</b>.",
        parse_mode="HTML"
    )

    # Notify all admins
    period_info = PERIODS[sub["period"]]
    user_link = f'<a href="tg://user?id={msg.from_user.id}">{msg.from_user.first_name}</a>'
    username_str = f"@{msg.from_user.username}" if msg.from_user.username else "нет username"

    from keyboards import kb_admin_approve
    caption = (
        f"💰 <b>Новая оплата!</b>\n\n"
        f"👤 Пользователь: {user_link} ({username_str})\n"
        f"🆔 ID: <code>{msg.from_user.id}</code>\n"
        f"📦 Период: <b>{period_info['label']}</b>\n"
        f"💵 Сумма: <b>{sub['price']} ₽</b>\n"
        f"🔖 Подписка №{sub_id}"
    )

    for admin_id in config.ADMIN_IDS:
        try:
            if msg.photo:
                await bot.send_photo(
                    admin_id,
                    photo=file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb_admin_approve(sub_id, msg.from_user.id)
                )
            else:
                await bot.send_document(
                    admin_id,
                    document=file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb_admin_approve(sub_id, msg.from_user.id)
                )
        except Exception:
            pass


# ── Restart / change period ─────────────────────────────────────────────────────

@router.callback_query(F.data == "restart")
async def cb_restart(call: CallbackQuery):
    await call.message.edit_text(
        "Выбери период подписки:",
        reply_markup=kb_choose_period()
    )
    await call.answer()
