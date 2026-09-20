from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

BUY_BUTTON = "🛒 خرید کانفیگ"
PLANS_BUTTON = "📦 پلن‌ها"
ORDERS_BUTTON = "🧾 سفارش‌های من"
SUPPORT_BUTTON = "🎧 پشتیبانی"
ABOUT_BUTTON = "ℹ️ درباره Virex"
BACK_BUTTON = "🔙 بازگشت"


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[BUY_BUTTON, PLANS_BUTTON], [ORDERS_BUTTON, SUPPORT_BUTTON], [ABOUT_BUTTON], [BACK_BUTTON]],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="یک گزینه را انتخاب کنید",
    )


def get_back_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(BACK_BUTTON, callback_data="menu:main")]])


def get_plan_keyboard(plans: list[object]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            f"🔹 {plan.traffic_gb} گیگ | {plan.duration_days} روز | {plan.price_toman:,} تومان",
            callback_data=f"plan:{plan.code}",
        )]
        for plan in plans
    ]
    rows.append([InlineKeyboardButton(BACK_BUTTON, callback_data="menu:main")])
    return InlineKeyboardMarkup(rows)


def get_confirmation_keyboard(code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تأیید و ثبت سفارش", callback_data=f"confirm:{code}")],
        [InlineKeyboardButton(BACK_BUTTON, callback_data="menu:plans")],
    ])
