from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.orders import my_orders, show_plans
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import get_main_menu_keyboard
from database.database import async_session_factory


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return
    async with async_session_factory() as session:
        await ensure_user_registered(session, update.effective_user)
    await update.message.reply_text(
        "به ربات فروش VPN وایرکس خوش آمدید 🌹\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_main_menu_keyboard(),
    )


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    if update.message.text == "🛒 خرید VPN":
        await show_plans(update, context)
    elif update.message.text == "📦 سفارش‌های من":
        await my_orders(update, context)
    else:
        await update.message.reply_text("لطفاً از منوی پایین یکی از گزینه‌ها را انتخاب کنید.")
