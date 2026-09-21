from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.main import get_main_menu_keyboard
from database.database import async_session_factory
from services.order import get_or_create_user
async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user: return
    async with async_session_factory() as session:
        user = await get_or_create_user(session, update.effective_user)
        if user.is_blocked: await update.message.reply_text("🚫 حساب شما مسدود است."); return
        balance = user.wallet_balance
    await update.message.reply_text(f"💰 موجودی کیف پول Virex: {balance:,} تومان\n\nبرای افزایش موجودی با پشتیبانی تماس بگیرید.", reply_markup=get_main_menu_keyboard())
