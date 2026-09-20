from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.database import async_session_factory
from services.order import get_pending_orders, update_order_status


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in settings.admin_ids


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return

    user_id = update.effective_user.id if update.effective_user else None
    if not is_admin(user_id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز. فقط مدیران می‌توانند وارد پنل شوند.")
        return

    async with async_session_factory() as session:
        orders = await get_pending_orders(session)

    if not orders:
        await update.message.reply_text("✅ هیچ سفارشی در انتظار بررسی وجود ندارد.")
        return

    lines = ["🛠 پنل مدیریت Virex\n", "📦 سفارش‌های در انتظار بررسی:"]
    for order in orders:
        user = order.user
        lines.append(
            f"\n━━━━━━━━━━━━\n"
            f"شماره سفارش: {order.order_uid}\n"
            f"شناسه سفارش: {order.id}\n"
            f"کاربر: {user.telegram_id if user else 'نامشخص'}\n"
            f"پلن: {order.plan_name}\n"
            f"حجم: {order.traffic_gb} گیگ\n"
            f"مبلغ: {order.price_toman:,} تومان\n"
            f"تأیید: /confirm {order.id}\n"
            f"رد: /reject {order.id}"
        )
    await update.message.reply_text("\n".join(lines))


async def _change_order(update: Update, context: ContextTypes.DEFAULT_TYPE, approved: bool) -> None:
    if update.message is None:
        return

    user_id = update.effective_user.id if update.effective_user else None
    if not is_admin(user_id):
        await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return

    if not context.args:
        await update.message.reply_text(
            "فرمت صحیح: /confirm ORDER_ID" if approved else "فرمت صحیح: /reject ORDER_ID"
        )
        return

    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("شناسه سفارش باید عددی باشد.")
        return

    async with async_session_factory() as session:
        order = await update_order_status(
            session,
            order_id,
            "approved" if approved else "rejected",
            "approved" if approved else "rejected",
        )

    if order is None:
        await update.message.reply_text("❌ سفارش موردنظر پیدا نشد.")
        return

    await update.message.reply_text(
        f"✅ سفارش {order.order_uid} با موفقیت تأیید شد." if approved else f"❌ سفارش {order.order_uid} رد شد."
    )


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_order(update, context, True)


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _change_order(update, context, False)
