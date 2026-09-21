from __future__ import annotations
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.main import WALLET_BUTTON, get_main_menu_keyboard
from database.database import async_session_factory
from database.models import User
from services.order import get_or_create_user

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user: return
    async with async_session_factory() as s:
        user = await get_or_create_user(s, update.effective_user)
        balance = user.wallet_balance
    await update.message.reply_text(f"💰 موجودی کیف پول Virex: {balance:,} تومان\n\nبرای افزایش موجودی با پشتیبانی تماس بگیرید.", reply_markup=get_main_menu_keyboard())
