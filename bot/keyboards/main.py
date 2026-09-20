from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🛒 خرید کانفیگ", callback_data="menu_buy"),
                InlineKeyboardButton("📦 پلن‌ها", callback_data="menu_plans"),
            ],
            [
                InlineKeyboardButton("📋 سفارش‌های من", callback_data="menu_orders"),
                InlineKeyboardButton("💬 پشتیبانی", callback_data="menu_support"),
            ],
        ]
    )


def get_plans_keyboard():
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
        buttons.append([InlineKeyboardButton(f"{plan[0]} • {plan[1].replace('gb','GB')}", callback_data=f"plan:{plan[1]}")])
    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")])
    return InlineKeyboardMarkup(buttons)


def get_back_keyboard(label: str = "🔙 بازگشت"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data="menu_main")]])
