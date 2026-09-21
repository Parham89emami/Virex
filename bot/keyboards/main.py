from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

BUY_BUTTON = "🛒 خرید کانفیگ"
ORDERS_BUTTON = "📦 سفارش‌های من"
WALLET_BUTTON = "💰 کیف پول"
SUPPORT_BUTTON = "🛟 پشتیبانی"
ADMIN_BUTTON = "⚙️ پنل مدیریت"
BACK_BUTTON = "🔙 بازگشت"
SUPPORT_URL = "https://t.me/Parham88e"


def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    rows = [[BUY_BUTTON, ORDERS_BUTTON], [WALLET_BUTTON], [SUPPORT_BUTTON]]
    if is_admin:
        rows.append([ADMIN_BUTTON])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, input_field_placeholder="انتخاب کنید")


def inline_menu(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data) for text, data in row] for row in rows])


def get_payment_keyboard() -> InlineKeyboardMarkup:
    return inline_menu([[('💳 کارت‌به‌کارت', 'pay:card'), ('💰 کیف پول', 'pay:wallet')]])


def get_support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton('👤 ارتباط با پشتیبانی', url=SUPPORT_URL)]])


def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True)
