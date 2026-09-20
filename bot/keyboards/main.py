from __future__ import annotations

from telegram import ReplyKeyboardMarkup


BUY_BUTTON = "🛒 خرید VPN"
ORDERS_BUTTON = "📦 سفارش‌های من"
SUPPORT_BUTTON = "💬 پشتیبانی"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BUY_BUTTON, ORDERS_BUTTON],
            [SUPPORT_BUTTON],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="یک گزینه را انتخاب کنید",
    )
