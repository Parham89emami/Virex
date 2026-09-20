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
                f"🔹 {plan.traffic_gb} گیگ | ۳۰ روز | {plan.price_toman:,} تومان",
                callback_data=f"plan:{plan.code}",
            )
        ]
        for plan in VPNService.get_plans()
    ]
    await update.message.reply_text(
        "📋 پلن موردنظر را انتخاب کنید:\n\n"
        "✅ همه پلن‌ها ۳۰ روزه هستند\n"
        "💳 پس از انتخاب، اطلاعات پرداخت نمایش داده می‌شود.",
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
        await query.edit_message_text("❌ پلن انتخاب‌شده معتبر نیست. لطفاً دوباره از منو انتخاب کنید.")
        return

    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        order = await create_order_for_user(session, user, plan)

    payment = PaymentService()
    await query.edit_message_text(
        "✅ سفارش شما ثبت شد.\n\n"
        + payment.payment_instructions(order.order_uid, order.price_toman)
    )


async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.effective_user is None:
        return

    async with async_session_factory() as session:
        orders = await get_all_orders_for_user(session, update.effective_user.id)

    if not orders:
        await update.message.reply_text(
            "📦 هنوز سفارشی ثبت نکرده‌اید.\n\nبرای شروع، روی «🛒 خرید VPN» بزنید."
        )
        return

    status_labels = {
        "pending": "⏳ در انتظار پرداخت",
        "pending_review": "🔎 در انتظار بررسی رسید",
        "approved": "✅ تأییدشده",
        "rejected": "❌ ردشده",
    }
    payment_labels = {
        "pending": "⏳ پرداخت نشده",
        "pending_review": "🔎 در حال بررسی",
        "approved": "✅ تأییدشده",
        "paid": "✅ پرداخت موفق",
        "rejected": "❌ ردشده",
    }

    lines = ["📦 سفارش‌های شما:"]
    for order in orders:
        lines.append(
            f"\n━━━━━━━━━━━━\n"
            f"🧾 شماره: {order.order_uid}\n"
            f"💾 حجم: {order.traffic_gb} گیگ | مدت: {order.duration_days} روز\n"
            f"💰 مبلغ: {order.price_toman:,} تومان\n"
            f"📌 سفارش: {status_labels.get(order.status, order.status)}\n"
            f"💳 پرداخت: {payment_labels.get(order.payment_status, order.payment_status)}"
        )
    await update.message.reply_text("\n".join(lines))
