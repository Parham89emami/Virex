from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import get_confirmation_keyboard, get_plan_keyboard
from database.database import async_session_factory
from services.order import create_order_for_user, get_all_orders_for_user
from services.payment import PaymentService
from services.vpn import VPNService


async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is not None:
        await update.message.reply_text(
            "📦 پلن‌های Virex\n\n"
            "قیمت‌ها و حجم‌ها به‌صورت شفاف در جدول زیر نمایش داده می‌شود:\n\n"
            "10GB = 49,000 تومان\n"
            "20GB = 68,000 تومان\n"
            "30GB = 87,000 تومان\n"
            "40GB = 106,000 تومان\n"
            "50GB = 125,000 تومان\n"
            "60GB = 144,000 تومان\n"
            "70GB = 163,000 تومان\n"
            "80GB = 182,000 تومان\n"
            "90GB = 201,000 تومان\n"
            "100GB = 220,000 تومان\n\n"
            "یکی از پلن‌ها را انتخاب کنید:",
            reply_markup=get_plan_keyboard(),
        )
        return

    query = update.callback_query
    if query is None:
        return
    await query.answer()
    await query.edit_message_text(
        "📦 پلن‌های Virex\n\n"
        "یکی از پلن‌ها را انتخاب کنید:",
        reply_markup=get_plan_keyboard(),
    )


async def confirm_plan_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None or update.effective_user is None:
        return
    await query.answer()

    data = (query.data or "").split(":", 1)
    if len(data) != 2 or data[0] != "confirm_order":
        await query.edit_message_text("درخواست نامعتبر است.")
        return

    plan = VPNService.get_plan_by_code(data[1])
    if plan is None:
        await query.edit_message_text("پلن انتخاب‌شده معتبر نیست.")
        return

    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        order = await create_order_for_user(session, user, plan)

    payment = PaymentService()
    await query.edit_message_text(
        payment.payment_instructions(order.order_uid, order.price_toman, order.plan_name, order.traffic_gb),
        reply_markup=None,
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

    summary = (
        "🧾 خلاصه سفارش\n\n"
        f"نام پلن: {plan.name}\n"
        f"حجم: {plan.traffic_gb} گیگ\n"
        f"مدت اعتبار: {plan.duration_days} روز\n"
        f"مبلغ: {plan.price_toman:,} تومان\n\n"
        "تأیید سفارش، شما را به مرحله پرداخت می‌برد."
    )
    await query.edit_message_text(summary, reply_markup=get_confirmation_keyboard(plan.code))


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return
    async with async_session_factory() as session:
        orders = await get_all_orders_for_user(session, update.effective_user.id)

    if not orders:
        await update.message.reply_text("شما هنوز سفارشی ثبت نکرده‌اید.\nبرای خرید، /start را بزنید و گزینه خرید کانفیگ را انتخاب کنید.")
        return

    lines = ["📋 سفارش‌های شما:\n"]
    for order in orders:
        status_label = PaymentService().get_status_label(order.payment_status)
        lines.append(
            f"🔹 شماره سفارش: {order.order_uid}\n"
            f"پلن: {order.plan_name}\n"
            f"حجم: {order.traffic_gb} گیگ | مدت: {order.duration_days} روز\n"
            f"مبلغ: {order.price_toman:,} تومان\n"
            f"وضعیت: {status_label}\n"
        )
    await update.message.reply_text("\n\n".join(lines))
