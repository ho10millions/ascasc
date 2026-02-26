from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import PERIODS


def kb_choose_period() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"📅 {info['label']} — {info['price']} ₽",
            callback_data=f"period:{key}"
        )]
        for key, info in PERIODS.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_paid(sub_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data=f"paid:{sub_id}")
    ]])


def kb_change_period() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Выбрать другой период", callback_data="restart")
    ]])


def kb_admin_approve(sub_id: int, user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✅ Одобрить",
            callback_data=f"approve:{sub_id}:{user_id}"
        ),
        InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"reject:{sub_id}:{user_id}"
        ),
    ]])
