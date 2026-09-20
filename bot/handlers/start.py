from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["🛒 خرید کانفیگ", "📦 پلن‌ها"],
            ["📋 سفارش‌های من", "💬 پشتیبانی"],
            ["🔙 بازگشت"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_plan_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for plan in [
        ("10GB", "10gb"),
        ("20GB", "20gb"),
        ("30GB", "30gb"),
        ("40GB", "40gb"),
        ("50GB", "50gb"),
        ("60GB", "60gb"),
        ("70GB", "70gb"),
        ("80GB", "80gb"),
        ("90GB", "90gb"),
        ("100GB", "100gb"),
    ]:
        buttons.append([InlineKeyboardButton(f"{plan[0]}", callback_data=f"plan:{plan[1]}")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_plans")])
    return InlineKeyboardMarkup(buttons)


def get_confirmation_keyboard(plan_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✅ تایید و ادامه", callback_data=f"confirm_order:{plan_code}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_plans")],
        ]
    )
