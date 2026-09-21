from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.orders import my_orders, show_plans
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import BACK_BUTTON, COUPON_BUTTON, SUPPORT_BUTTON, get_main_menu_keyboard, get_support_keyboard
from config.settings import settings
from database.database import async_session_factory


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return
    context.user_data.clear()
    async with async_session_factory() as session:
        await ensure_user_registered(session, update.effective_user)
    await update.message.reply_text(
        "✨ به ربات رسمی Virex خوش آمدید!\n\n"
        "فروش امن کانفیگ VPN با پرداخت آسان و تحویل مطمئن پس از تأیید سفارش.\n\n"
        "از منوی زیر گزینه موردنظر خود را انتخاب کنید:",
        reply_markup=get_main_menu_keyboard(),
    )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        await update.message.reply_text(
            "🛟 پشتیبانی Virex\n\n"
            "اگر سوال، مشکل در خرید، پرداخت یا دریافت کانفیگ دارید، با پشتیبانی در ارتباط باشید:\n\n"
            "👤 @Parham88e",
            reply_markup=get_support_keyboard(),
        )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await my_orders(update, context)


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text in {"🛒 خرید کانفیگ", "🛒 خرید VPN", "خرید VPN", "📦 محصولات"}:
        await show_plans(update, context)
    elif text in {"📦 سفارش‌های من", "سفارش‌های من"}:
        await my_orders(update, context)
    elif text in {"💰 کیف پول", "کیف پول"}:
        from bot.handlers.wallet import wallet
        await wallet(update, context)
    elif text in {COUPON_BUTTON, "کد تخفیف"}:
        await update.message.reply_text(
            "🎟 برای استفاده از کد تخفیف، ابتدا محصول موردنظر را انتخاب کنید؛ سپس کد خود را وارد کنید.",
            reply_markup=get_main_menu_keyboard(),
        )
        await show_plans(update, context)
    elif text in {SUPPORT_BUTTON, "💬 پشتیبانی", "پشتیبانی"}:
        await support_command(update, context)
    elif text in {BACK_BUTTON, "بازگشت"}:
        await start(update, context)
    else:
        await update.message.reply_text("لطفاً یکی از گزینه‌های منو را انتخاب کنید.", reply_markup=get_main_menu_keyboard())
