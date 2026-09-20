from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.main import get_main_menu_keyboard
from database.database import async_session_factory
from services.order import get_latest_pending_order_for_user, update_order_review


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    if update.message.photo:
        file_id, file_name, receipt_type = update.message.photo[-1].file_id, "receipt.jpg", "photo"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name or "receipt"
        receipt_type = "document"
    else:
        return
    async with async_session_factory() as session:
        order = await get_latest_pending_order_for_user(session, update.effective_user.id)
        if order is None:
            await update.message.reply_text("❌ سفارش قابل پرداختی پیدا نشد.", reply_markup=get_main_menu_keyboard())
            return
        await update_order_review(session, order, file_id, file_name, receipt_type)
    await update.message.reply_text("✅ رسید برای بررسی ادمین ارسال شد.", reply_markup=get_main_menu_keyboard())
