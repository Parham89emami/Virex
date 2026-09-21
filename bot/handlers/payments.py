from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.main import get_main_menu_keyboard
from config.settings import settings
from database.database import async_session_factory
from services.order import pending_order, review_order

logger = logging.getLogger(__name__)


async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    if update.message.photo:
        file_id, file_name = update.message.photo[-1].file_id, "receipt.jpg"
    elif update.message.document:
        file_id, file_name = update.message.document.file_id, update.message.document.file_name or "receipt"
    else:
        return
    async with async_session_factory() as session:
        order = await pending_order(session, update.effective_user.id)
        if not order:
            await update.message.reply_text("❌ سفارش پرداخت‌نشده‌ای برای ثبت رسید ندارید.", reply_markup=get_main_menu_keyboard())
            return
        await review_order(session, order, file_id, file_name)
    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(admin_id, f"🧾 رسید جدید Virex\nسفارش: {order.order_uid}\nشناسه داخلی برای تأیید/رد: {order.id}\n\n/confirm {order.id}\n/reject {order.id}")
            if update.message.photo:
                await context.bot.send_photo(admin_id, file_id, caption=f"رسید سفارش {order.order_uid}")
            else:
                await context.bot.send_document(admin_id, file_id, caption=f"رسید سفارش {order.order_uid}")
        except Exception:
            logger.exception("Could not forward receipt to admin %s", admin_id)
    await update.message.reply_text("✅ رسید دریافت شد و پس از بررسی مدیر، کانفیگ ارسال می‌شود.", reply_markup=get_main_menu_keyboard())
