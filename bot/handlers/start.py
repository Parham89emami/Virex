from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.orders import my_orders, show_plans
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import (
    BUY_BUTTON,
    ORDERS_BUTTON,
    SUPPORT_BUTTON,
    get_main_menu_keyboard,
)
from database.database import async_session_factory


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user is None or update.message is None:
        return

    async with async_session_factory() as session:
        await ensure_user_registered(session, update.effective_user)

    await update.message.reply_text(
        "🚀 به Virex خوش آمدید!\n\n"
        "خرید VPN سریع و ساده است. ابتدا یک گزینه را انتخاب کنید:\n"
        "• خرید VPN برای دیدن پلن‌ها\n"
        "• سفارش‌های من برای پیگیری خریدها\n"
        "• پشتیبانی برای دریافت راهنمایی",
        reply_markup=get_main_menu_keyboard(),
    )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "💬 پشتیبانی Virex\n\n"
        "برای راهنمایی درباره انتخاب پلن، پرداخت یا وضعیت سفارش، همین‌جا پیام خود را ارسال کنید.\n\n"
        "⏱ رسیدگی به درخواست‌ها پس از بررسی انجام می‌شود.",
        reply_markup=get_main_menu_keyboard(),
    )


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return

    text = update.message.text.strip()
    if text in {BUY_BUTTON, "خرید VPN", "🛒 خرید کانفیگ", "خرید کانفیگ", "📦 پلن‌ها", "پلن‌ها"}:
        await show_plans(update, context)
    elif text in {ORDERS_BUTTON, "سفارش‌های من", "سفارشات من"}:
        await my_orders(update, context)
    elif text in {SUPPORT_BUTTON, "پشتیبانی"}:
        await support_command(update, context)
    else:
        await update.message.reply_text(
            "لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
            reply_markup=get_main_menu_keyboard(),
        )
