from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

BUY_BUTTON = "🛒 خرید کانفیگ"
ORDERS_BUTTON = "📦 سفارش‌های من"
WALLET_BUTTON = "💰 کیف پول"
COUPON_BUTTON = "🎟 کد تخفیف"
SUPPORT_BUTTON = "🛟 پشتیبانی"
BACK_BUTTON = "🔙 بازگشت"
SUPPORT_USERNAME = "@Parham88e"
SUPPORT_URL = "https://t.me/Parham88e"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BUY_BUTTON, ORDERS_BUTTON], [WALLET_BUTTON, COUPON_BUTTON], [SUPPORT_BUTTON]],
        resize_keyboard=True,
        input_field_placeholder="انتخاب کنید",
    )


def get_support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("👤 ارتباط با پشتیبانی", url=SUPPORT_URL)]]
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True)
