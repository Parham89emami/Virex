from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.handlers.orders import show_plans
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import ABOUT_BUTTON, BACK_BUTTON, BUY_BUTTON, ORDERS_BUTTON, PLANS_BUTTON, SUPPORT_BUTTON, get_main_menu_keyboard, get_plan_keyboard
from config.settings import settings
from database.database import async_session_factory
from services.order import cancel_all_orders_for_user, cancel_order_for_user, get_all_orders_for_user
from services.vpn import VPNService


def _cancel_all_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("🗑 پاک کردن همه سفارش‌ها", callback_data="cancel_all:confirm")]])


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    async with async_session_factory() as session:
        orders = await get_all_orders_for_user(session, update.effective_user.id)
    if not orders:
        await update.message.reply_text("🧾 هنوز سفارشی ندارید.", reply_markup=get_main_menu_keyboard())
        return
    labels = {"pending": "⏳ در انتظار پرداخت", "pending_review": "🔎 در انتظار بررسی", "approved": "✅ تأییدشده", "rejected": "❌ ردشده", "cancelled": "🚫 لغوشده"}
    lines = ["🧾 سفارش‌های شما:"]
    cancellable = False
    for order in orders:
        lines.append(f"\n━━━━━━━━━━━━\n🆔 {order.order_uid}\n📦 {order.traffic_gb} گیگ | {order.duration_days} روز\n💰 {order.price_toman:,} تومان\n📌 {labels.get(order.status, order.status)}")
        cancellable = cancellable or order.status in {"pending", "pending_review"}
    await update.message.reply_text(
        "\n".join(lines),
        reply_markup=_cancel_all_keyboard() if cancellable else get_main_menu_keyboard(),
    )


async def confirm_cancel_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله، همه لغو شوند", callback_data="cancel_all:yes")],
        [InlineKeyboardButton("↩️ انصراف", callback_data="cancel_all:no")],
    ]))


async def cancel_all_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if query is None or user is None:
        return
    await query.answer()
    if (query.data or "").endswith(":no"):
        await query.edit_message_text("✅ سفارش‌ها لغو نشدند.")
        return
    async with async_session_factory() as session:
        count = await cancel_all_orders_for_user(session, user.id)
    await query.edit_message_text(
        f"✅ {count} سفارش قابل لغو، لغو شد." if count else "ℹ️ سفارش قابل لغوی پیدا نشد."
    )


async def confirm_cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    try:
        order_id = int((query.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await query.edit_message_text("❌ سفارش نامعتبر است.")
        return
    await query.edit_message_text("⚠️ آیا از لغو این سفارش مطمئن هستید؟", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله، لغو شود", callback_data=f"cancel:yes:{order_id}")],
        [InlineKeyboardButton("↩️ انصراف", callback_data=f"cancel:no:{order_id}")],
    ]))


async def cancel_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.effective_user
    if query is None or user is None:
        return
    await query.answer()
    if (query.data or "").startswith("cancel:no:"):
        await query.edit_message_text("✅ لغو سفارش انجام نشد.")
        return
    try:
        order_id = int((query.data or "").rsplit(":", 1)[-1])
    except ValueError:
        await query.edit_message_text("❌ سفارش نامعتبر است.")
        return
    async with async_session_factory() as session:
        order = await cancel_order_for_user(session, user.id, order_id)
    await query.edit_message_text(f"✅ سفارش {order.order_uid} لغو شد." if order else "❌ سفارش قابل لغو نیست.")
