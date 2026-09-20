from __future__ import annotations

from telegram import ReplyKeyboardMarkup

BUY_BUTTON = "🛒 خرید VPN"
ORDERS_BUTTON = "📦 سفارش‌های من"
SUPPORT_BUTTON = "💬 پشتیبانی"
BACK_BUTTON = "🔙 بازگشت"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BUY_BUTTON, ORDERS_BUTTON],
            [SUPPORT_BUTTON],
            [BACK_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="انتخاب کنید",
    )


def get_back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BACK_BUTTON]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
