from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

BUY_BUTTON = "🛒 خرید کانفیگ"
ORDERS_BUTTON = "📦 سفارش‌های من"
WALLET_BUTTON = "💰 کیف پول"
SUPPORT_BUTTON = "🛟 پشتیبانی"
BACK_BUTTON = "🔙 بازگشت"
SUPPORT_URL = "https://t.me/Parham88e"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BUY_BUTTON, ORDERS_BUTTON], [WALLET_BUTTON], [SUPPORT_BUTTON]],
        resize_keyboard=True,
        input_field_placeholder="انتخاب کنید",
    )


def get_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("💳 کارت‌به‌کارت", callback_data="pay:card"),
            InlineKeyboardButton("💰 کیف پول", callback_data="pay:wallet"),
        ]]
    )


def get_support_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("👤 ارتباط با پشتیبانی", url=SUPPORT_URL)]]
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[BACK_BUTTON]], resize_keyboard=True)
