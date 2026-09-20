from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.main import get_back_inline_keyboard, get_confirmation_keyboard, get_plan_keyboard, get_main_menu_keyboard
from bot.handlers.users import ensure_user_registered
from database.database import async_session_factory
from services.order import create_order_for_user, get_all_orders_for_user
from services.payment import PaymentService
from services.vpn import VPNService


async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    await update.message.reply_text(
        "📦 پلن موردنظر را انتخاب کنید:\n\n✅ اعتبار همه پلن‌ها: ۳۰ روز",
        reply_markup=get_plan_keyboard(VPNService.get_plans()),
    )


async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()
    plan = VPNService.get_plan_by_code((query.data or "").split(":", 1)[-1])
    if plan is None:
        await query.edit_message_text("❌ پلن نامعتبر است.", reply_markup=get_back_inline_keyboard())
        return
    context.user_data["selected_plan"] = plan.code
    await query.edit_message_text(
        f"📋 جزئیات پلن\n\n📦 حجم: {plan.traffic_gb} گیگ\n⏱ مدت: {plan.duration_days} روز\n💰 قیمت: {plan.price_toman:,} تومان\n\nثبت سفارش؟",
        reply_markup=get_confirmation_keyboard(plan.code),
    )


async def confirm_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return
    await query.answer()
    plan = VPNService.get_plan_by_code((query.data or "").split(":", 1)[-1])
    if plan is None:
        await query.edit_message_text("❌ پلن نامعتبر است.", reply_markup=get_back_inline_keyboard())
        return
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        order, created = await create_order_for_user(session, user, plan)
    prefix = "✅ سفارش جدید ثبت شد." if created else "ℹ️ یک سفارش فعال برای شما وجود دارد."
    await query.edit_message_text(prefix + "\n\n" + PaymentService().payment_instructions(order.order_uid, order.price_toman), reply_markup=get_back_inline_keyboard())


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    async with async_session_factory() as session:
        orders = await get_all_orders_for_user(session, update.effective_user.id)
    if not orders:
        await update.message.reply_text("🧾 هنوز سفارشی ندارید.", reply_markup=get_main_menu_keyboard())
        return
    lines = ["🧾 سفارش‌های شما:"]
    for order in orders:
        lines.append(f"\n━━━━━━━━━━━━\n🆔 {order.order_uid}\n📦 {order.traffic_gb} گیگ | {order.duration_days} روز\n💰 {order.price_toman:,} تومان\n📌 {order.status}\n💳 {order.payment_status}")
    await update.message.reply_text("\n".join(lines), reply_markup=get_main_menu_keyboard())
