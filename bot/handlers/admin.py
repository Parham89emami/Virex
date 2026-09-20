from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.main import get_main_menu_keyboard
from config.settings import settings
from database.database import async_session_factory
from services.order import get_order_stats, get_pending_orders, update_order_status


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
    lines = ["🛠 داشبورد مدیریت Virex", "━━━━━━━━━━━━", f"👥 کاربران: {stats['users']}", f"🛒 سفارش‌ها: {stats['orders']}", f"💳 در انتظار بررسی: {len(orders)}", f"✅ تأییدشده: {stats['approved']}", f"❌ ردشده: {stats['rejected']}", f"💰 فروش تأییدشده: {stats['sales']:,} تومان"]
    if orders:
        lines.append("\n📦 سفارش‌های در انتظار:")
        for order in orders:
            user = order.user.telegram_id if order.user else "نامشخص"
            lines.append(f"\n🆔 {order.id} | {order.order_uid}\n👤 {user}\n📦 {order.traffic_gb} گیگ | 💰 {order.price_toman:,} تومان\n✅ /confirm {order.id}\n❌ /reject {order.id} [دلیل]")
    await update.message.reply_text("\n".join(lines), reply_markup=get_main_menu_keyboard())


async def _change_order(update: Update, context: ContextTypes.DEFAULT_TYPE, approved: bool) -> None:
    if update.message is None or not is_admin(update.effective_user.id if update.effective_user else None):
        if update.message:
            await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return
    if not context.args:
        await update.message.reply_text("فرمت صحیح: /confirm ORDER_ID" if approved else "فرمت صحیح: /reject ORDER_ID دلیل")
        return
    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("شناسه سفارش باید عددی باشد.")
        return
    if not approved and len(context.args) < 2:
        await update.message.reply_text("برای رد سفارش، دلیل را هم وارد کنید.")
        return
    async with async_session_factory() as session:
        order = await update_order_status(session, order_id, approved)
    if order is None:
        await update.message.reply_text("سفارش پیدا نشد یا قبلاً بررسی شده است.")
        return
    await update.message.reply_text(f"{'✅ تأیید شد' if approved else '❌ رد شد'}: {order.order_uid}")


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_order(update, context, True)


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_order(update, context, False)
