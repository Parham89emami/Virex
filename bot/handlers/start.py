from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.orders import show_plans
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import (
    ABOUT_BUTTON,
    BACK_BUTTON,
    BUY_BUTTON,
    ORDERS_BUTTON,
    PLANS_BUTTON,
    SUPPORT_BUTTON,
    get_main_menu_keyboard,
    get_plan_keyboard,
)
from config.settings import settings
from database.database import async_session_factory
from services.order import get_all_orders_for_user
from services.vpn import VPNService


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    async with async_session_factory() as session:
        await ensure_user_registered(session, update.effective_user)
    await update.message.reply_text(
        "🚀 به Virex خوش آمدید!\n\nیک گزینه را انتخاب کنید:",
        reply_markup=get_main_menu_keyboard(),
    )


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        f"🎧 پشتیبانی Virex\n\nارتباط با پشتیبانی: {settings.support_contact}",
        reply_markup=get_main_menu_keyboard(),
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "ℹ️ درباره Virex\n\nفروش امن و ساده سرویس VPN با بررسی دستی پرداخت‌ها.",
        reply_markup=get_main_menu_keyboard(),
    )


async def orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    async with async_session_factory() as session:
        orders = await get_all_orders_for_user(session, update.effective_user.id)
    if not orders:
        await update.message.reply_text("🧾 هنوز سفارشی ندارید.", reply_markup=get_main_menu_keyboard())
        return
    labels = {
        "pending": "⏳ در انتظار پرداخت", "pending_review": "🔎 در انتظار بررسی",
        "approved": "✅ تأییدشده", "rejected": "❌ ردشده",
    }
    lines = ["🧾 سفارش‌های شما:"]
    for order in orders:
        lines.append(
            f"\n━━━━━━━━━━━━\n🆔 {order.order_uid}\n"
            f"📦 {order.traffic_gb} گیگ | {order.duration_days} روز\n"
            f"💰 {order.price_toman:,} تومان\n"
            f"📌 {labels.get(order.status, order.status)}"
        )
    await update.message.reply_text("\n".join(lines), reply_markup=get_main_menu_keyboard())


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline navigation back to the reply-keyboard main menu."""
    query = update.callback_query
    if query is None or query.message is None:
        return
    await query.answer()
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(
        "🏠 منوی اصلی Virex",
        reply_markup=get_main_menu_keyboard(),
    )


async def plans_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Render the plan list when the user presses an inline back button."""
    query = update.callback_query
    if query is None or query.message is None:
        return
    await query.answer()
    await query.edit_message_text(
        "📦 پلن موردنظر را انتخاب کنید:\n\n✅ اعتبار همه پلن‌ها: ۳۰ روز",
        reply_markup=get_plan_keyboard(VPNService.get_plans()),
    )


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or not update.message.text:
        return
    text = update.message.text.strip()
    if text in {BUY_BUTTON, PLANS_BUTTON, "خرید VPN", "خرید کانفیگ", "پلن‌ها"}:
        await show_plans(update, context)
    elif text in {ORDERS_BUTTON, "سفارش‌های من", "سفارشات من"}:
        await orders_command(update, context)
    elif text in {SUPPORT_BUTTON, "پشتیبانی"}:
        await support_command(update, context)
    elif text == ABOUT_BUTTON:
        await about_command(update, context)
    elif text in {BACK_BUTTON, "بازگشت", "منو اصلی"}:
        await start(update, context)
    else:
        await update.message.reply_text("لطفاً یک گزینه از منو انتخاب کنید.", reply_markup=get_main_menu_keyboard())
