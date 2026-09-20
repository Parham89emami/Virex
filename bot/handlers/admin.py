from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.keyboards.main import get_main_menu_keyboard
from config.settings import settings
from database.database import async_session_factory
from services.order import get_order_by_id, get_order_stats, get_pending_orders, update_order_status

logger = logging.getLogger(__name__)


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in settings.admin_ids


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or not is_admin(update.effective_user.id if update.effective_user else None):
        if update.message:
            await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    async with async_session_factory() as session:
        stats = await get_order_stats(session)
        orders = await get_pending_orders(session)

    lines = [
        "🛠 داشبورد مدیریت Virex", "━━━━━━━━━━━━",
        f"👥 کاربران: {stats['users']}", f"🛒 سفارش‌ها: {stats['orders']}",
        f"💳 در انتظار بررسی: {len(orders)}", f"✅ تأییدشده: {stats['approved']}",
        f"❌ ردشده: {stats['rejected']}", f"💰 فروش تأییدشده: {stats['sales']:,} تومان",
    ]
    buttons: list[list[InlineKeyboardButton]] = []
    for order in orders:
        user = order.user.telegram_id if order.user else "نامشخص"
        lines.append(
            f"\n🆔 {order.id} | {order.order_uid}\n👤 {user}\n"
            f"📦 {order.traffic_gb} گیگ | 💰 {order.price_toman:,} تومان\n"
            f"✅ /confirm {order.id}\n❌ /reject {order.id} دلیل"
        )
        if order.receipt_file_id:
            buttons.append([InlineKeyboardButton(
                f"🧾 مشاهده رسید {order.id}", callback_data=f"admin:receipt:{order.id}"
            )])
    if not orders:
        lines.append("\n✅ سفارش در انتظار بررسی وجود ندارد.")

    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else get_main_menu_keyboard(),
    )


async def view_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    admin_id = update.effective_user.id if update.effective_user else None
    if query is None or not is_admin(admin_id):
        if query:
            await query.answer("⛔ دسترسی غیرمجاز.", show_alert=True)
        return
    await query.answer()
    try:
        order_id = int((query.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await query.answer("شناسه سفارش نامعتبر است.", show_alert=True)
        return

    async with async_session_factory() as session:
        order = await get_order_by_id(session, order_id)
    if order is None or not order.receipt_file_id:
        await query.answer("برای این سفارش رسیدی ثبت نشده است.", show_alert=True)
        return

    caption = f"🧾 رسید سفارش {order.order_uid}"
    file_name = (order.receipt_file_name or "").lower()
    if file_name.endswith((".jpg", ".jpeg", ".png", ".webp")):
        await context.bot.send_photo(chat_id=admin_id, photo=order.receipt_file_id, caption=caption)
    else:
        await context.bot.send_document(chat_id=admin_id, document=order.receipt_file_id, caption=caption)


async def _change_order(update: Update, context: ContextTypes.DEFAULT_TYPE, approved: bool) -> None:
    admin_id = update.effective_user.id if update.effective_user else None
    if update.message is None or not is_admin(admin_id):
        if update.message:
            await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return
    if not context.args:
        await update.message.reply_text(
            "فرمت صحیح: /confirm ORDER_ID" if approved else "فرمت صحیح: /reject ORDER_ID دلیل"
        )
        return
    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("شناسه سفارش باید عددی باشد.")
        return
    reason = " ".join(context.args[1:]).strip() if not approved else None
    if not approved and not reason:
        await update.message.reply_text("برای رد سفارش، دلیل را هم وارد کنید.")
        return

    async with async_session_factory() as session:
        order = await update_order_status(session, order_id, approved, admin_id or 0, reason)
    if order is None:
        await update.message.reply_text("سفارش پیدا نشد یا قبلاً بررسی شده است.")
        return

    try:
        if order.user is not None:
            if approved:
                message = (
                    f"✅ سفارش {order.order_uid} تأیید شد.\n\n"
                    "تحویل خودکار کانفیگ تا زمان اتصال Marzban فعال نیست."
                )
            else:
                message = f"❌ سفارش {order.order_uid} رد شد.\nدلیل: {reason}"
            await context.bot.send_message(chat_id=order.user.telegram_id, text=message)
    except Exception:
        logger.exception("Order notification failed for order_id=%s", order_id)

    await update.message.reply_text(
        f"{'✅ تأیید شد' if approved else '❌ رد شد'}: {order.order_uid}"
    )


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_order(update, context, True)


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_order(update, context, False)
