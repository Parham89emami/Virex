from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.orders import my_orders, show_plans
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import BACK_BUTTON, get_main_menu_keyboard
from config.settings import settings
from database.database import async_session_factory


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    async with async_session_factory() as session:
        await ensure_user_registered(session, update.effective_user)

    await update.message.reply_text(
        "🚀 به Virex خوش آمدید!\n\n"
        "خرید VPN سریع و ساده است. یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=get_main_menu_keyboard(),
    )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    await update.message.reply_text(
        "💬 پشتیبانی Virex\n\n"
        f"برای تماس با پشتیبانی: {settings.support_contact}\n\n"
        "اگر درباره سفارش، پرداخت یا پلن‌ها سؤال داری، پیام بده.",
        reply_markup=get_main_menu_keyboard(),
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await my_orders(update, context)


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return

    text = update.message.text.strip()
    if text in {"🛒 خرید VPN", "🛒 خرید کانفیگ", "خرید VPN", "خرید کانفیگ", "پلن‌ها", "📦 پلن‌ها"}:
        await show_plans(update, context)
    elif text in {"📦 سفارش‌های من", "سفارش‌های من", "سفارشات من"}:
        await orders_command(update, context)
    elif text in {"💬 پشتیبانی", "پشتیبانی"}:
        await support_command(update, context)
    elif text in {BACK_BUTTON, "بازگشت", "منو اصلی"}:
        await start(update, context)
    else:
        await update.message.reply_text(
            "لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
            reply_markup=get_main_menu_keyboard(),
        )
