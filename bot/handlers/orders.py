from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.orders import my_orders, show_plans
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import get_main_menu_keyboard
from config.settings import settings
from database.database import async_session_factory


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    async with async_session_factory() as session:
        await ensure_user_registered(session, update.effective_user)

    await update.message.reply_text(
        "🚀 به Virex خوش آمدید\n\n"
        "Virex یک سرویس حرفه‌ای برای خرید VPN با قیمت‌های شفاف و پشتیبانی سریع است.\n\n"
        "برای شروع، یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_main_menu_keyboard(),
    )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "💬 پشتیبانی Virex\n\n"
        f"برای تماس و پاسخ‌گویی: {settings.support_contact}\n\n"
        "اگر نیاز به راهنمایی داری، همین حالا پیام بده."
    )


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return

    text = update.message.text.strip()
    if text in {"🛒 خرید VPN", "🛒 خرید کانفیگ", "خرید کانفیگ", "خرید VPN", "پلن‌ها"}:
        await show_plans(update, context)
    elif text in {"📦 سفارش‌های من", "سفارش‌های من", "سفارشات من"}:
        await my_orders(update, context)
    elif text in {"💬 پشتیبانی", "پشتیبانی"}:
        await support_command(update, context)
    elif text in {"🔙 بازگشت", "بازگشت", "منو اصلی"}:
        await start(update, context)
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های منو را انتخاب کنید.")
