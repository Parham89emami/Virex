from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from database.database import async_session_factory
from services.order import get_latest_pending_order_for_user, update_order_review


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_name = "receipt.jpg"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name or "receipt"
    else:
        return

    async with async_session_factory() as session:
        order = await get_latest_pending_order_for_user(session, update.effective_user.id)
        if order is None:
            await update.message.reply_text("❌ سفارش پرداخت‌نشده‌ای برای ثبت رسید پیدا نشد.")
            return
        await update_order_review(session, order, file_id, file_name)

    await update.message.reply_text(
        "✅ رسید دریافت شد و برای بررسی ارسال شد.\n"
        "پس از تأیید ادمین، وضعیت سفارش در بخش «سفارش���های من» تغییر می‌کند."
    )
