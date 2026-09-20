from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.handlers.users import ensure_user_registered
from database.database import async_session_factory
from services.order import create_order_for_user, get_all_orders_for_user
from services.payment import PaymentService
from services.vpn import VPNService


async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    buttons = [
        [
            InlineKeyboardButton(
                f"{plan.traffic_gb} گیگ | ۳۰ روز | {plan.price_toman:,} تومان",
                callback_data=f"plan:{plan.code}",
            )
        ]
        for plan in VPNService.get_plans()
    ]
    await update.message.reply_text(
        "📋 پلن موردنظر خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return
    await query.answer()
    code = (query.data or "").split(":", 1)[-1]
    plan = VPNService.get_plan_by_code(code)
    if plan is None:
        await query.edit_message_text("پلن انتخاب‌شده معتبر نیست.")
        return
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        order = await create_order_for_user(session, user, plan)
    payment = PaymentService()
    await query.edit_message_text(payment.payment_instructions(order.order_uid, order.price_toman))


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    async with async_session_factory() as session:
        orders = await get_all_orders_for_user(session, update.effective_user.id)
    if not orders:
        await update.message.reply_text("شما هنوز سفارشی ثبت نکرده‌اید.")
        return
    lines = ["📦 سفارش‌های شما:\n"]
    for order in orders:
        lines.append(
            f"🔹 شماره: {order.order_uid}\n"
            f"پلن: {order.plan_name}\n"
            f"حجم: {order.traffic_gb} گیگ | مدت: {order.duration_days} روز\n"
            f"مبلغ: {order.price_toman:,} تومان\n"
            f"وضعیت سفارش: {order.status}\nوضعیت پرداخت: {order.payment_status}"
        )
    await update.message.reply_text("\n\n".join(lines))
