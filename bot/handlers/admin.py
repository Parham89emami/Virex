from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from config.settings import settings
from database.database import async_session_factory
from database.models import Coupon, Order, Product, User, VPNConfig, WalletTransaction
from services.order import approve_and_deliver

logger = logging.getLogger(__name__)


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in settings.admin_ids


def denied(update: Update) -> bool:
    return not is_admin(update.effective_user.id if update.effective_user else None)


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message: return
    if denied(update): await update.message.reply_text("⛔ دسترسی غیرمجاز."); return
    async with async_session_factory() as s:
        total_users = (await s.execute(select(func.count(User.id)))).scalar() or 0
        total_orders = (await s.execute(select(func.count(Order.id)))).scalar() or 0
        completed = (await s.execute(select(func.count(Order.id)).where(Order.status == "completed"))).scalar() or 0
        pending = (await s.execute(select(func.count(Order.id)).where(Order.status == "pending_review"))).scalar() or 0
        sales = (await s.execute(select(func.coalesce(func.sum(Order.price_toman), 0)).where(Order.status == "completed"))).scalar() or 0
        stock = (await s.execute(select(func.count(VPNConfig.id)).where(VPNConfig.status == "available"))).scalar() or 0
    await update.message.reply_text(f"👑 پنل مدیریت Virex\n👥 کاربران: {total_users}\n🧾 سفارش‌ها: {total_orders}\n✅ تکمیل‌شده: {completed}\n⏳ در انتظار بررسی: {pending}\n💰 فروش: {sales:,} تومان\n🔐 موجودی: {stock}\n\nمحصولات: /products\nموجودی: /configs")


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as s:
        order, config = await approve_and_deliver(s, int(context.args[0]))
        user = await s.get(User, order.user_id) if order and config else None
    if not order: await update.message.reply_text("❌ سفارش پیدا نشد."); return
    if not config: await update.message.reply_text("⚠️ کانفیگ available برای این محصول وجود ندارد؛ سفارش تکمیل نشد."); return
    try:
        await context.bot.send_message(user.telegram_id, f"✅ پرداخت سفارش {order.order_uid} تأیید شد!\n\n🔐 کانفیگ Virex شما:\n{config.config_text}")
    except Exception:
        logger.exception("Delivery failed for order %s", order.id)
    await update.message.reply_text(f"✅ سفارش {order.order_uid} تکمیل و کانفیگ به کاربر ارسال شد.")


async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as s:
        order = await s.get(Order, int(context.args[0]))
        if order and order.payment_status == "pending_review":
            order.status = order.payment_status = "rejected"
            if order.payment_method == "wallet":
                user = await s.get(User, order.user_id)
                user.wallet_balance += order.price_toman
                s.add(WalletTransaction(user_id=user.id, amount=order.price_toman, transaction_type="refund", description=f"بازگشت سفارش {order.order_uid}"))
            await s.commit()
    await update.message.reply_text("❌ سفارش رد شد و در صورت پرداخت با کیف پول، مبلغ بازگردانده شد." if order else "❌ سفارش پیدا نشد.")


async def products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update): return
    async with async_session_factory() as s: rows = (await s.execute(select(Product).order_by(Product.volume_gb))).scalars().all()
    await update.message.reply_text("📦 محصولات Virex:\n" + ("\n".join(f"{p.id}: {p.volume_gb}GB | {p.duration_days} روز | {p.price:,} تومان | {'فعال' if p.is_active else 'غیرفعال'}" for p in rows) if rows else "محصولی وجود ندارد."))


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 4: return
    try: volume, days, price = map(int, context.args[-3:]); name = " ".join(context.args[:-3])
    except ValueError: await update.message.reply_text("فرمت: /addproduct نام حجم مدت قیمت"); return
    async with async_session_factory() as s: s.add(Product(name=name, volume_gb=volume, duration_days=days, price=price)); await s.commit()
    await update.message.reply_text("✅ محصول اضافه شد.")


async def edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 4: return
    try: product = None; pid, volume, days, price = map(int, context.args[:4])
    except ValueError: await update.message.reply_text("فرمت: /editproduct شناسه حجم مدت قیمت"); return
    async with async_session_factory() as s:
        product = await s.get(Product, pid)
        if product: product.volume_gb, product.duration_days, product.price = volume, days, price; await s.commit()
    await update.message.reply_text("✅ محصول ویرایش شد." if product else "❌ محصول پیدا نشد.")


async def toggle_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as s:
        product = await s.get(Product, int(context.args[0]))
        if product: product.is_active = not product.is_active; await s.commit()
    await update.message.reply_text("✅ وضعیت محصول تغییر کرد." if product else "❌ محصول پیدا نشد.")


async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as s:
        product = await s.get(Product, int(context.args[0]))
        if product: product.is_active = False; await s.commit()
    await update.message.reply_text("✅ محصول غیرفعال شد." if product else "❌ محصول پیدا نشد.")


async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 2: return
    try: product_id = int(context.args[0])
    except ValueError: await update.message.reply_text("فرمت: /addconfig شناسه_محصول متن_کانفیگ"); return
    async with async_session_factory() as s: s.add(VPNConfig(product_id=product_id, config_text=" ".join(context.args[1:]))); await s.commit()
    await update.message.reply_text("✅ کانفیگ available اضافه شد.")


async def configs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update): return
    async with async_session_factory() as s: rows = (await s.execute(select(VPNConfig).order_by(VPNConfig.id))).scalars().all()
    await update.message.reply_text("🔐 موجودی Virex:\n" + ("\n".join(f"{c.id}: محصول {c.product_id} | {c.status}" for c in rows) if rows else "موجودی خالی است."))


async def delete_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as s:
        config = await s.get(VPNConfig, int(context.args[0]))
        if config and config.status == "available": await s.delete(config); await s.commit()
    await update.message.reply_text("✅ کانفیگ حذف شد." if config else "❌ کانفیگ پیدا نشد یا فروخته شده است.")


async def user_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as s:
        user = (await s.execute(select(User).where(User.telegram_id == int(context.args[0])))).scalar_one_or_none()
        count = (await s.execute(select(func.count(Order.id)).where(Order.user_id == user.id))).scalar() if user else 0
    await update.message.reply_text(f"👤 {user.telegram_id}\nسفارش‌ها: {count}\nکیف پول: {user.wallet_balance:,}\nمسدود: {'بله' if user.is_blocked else 'خیر'}" if user else "کاربر پیدا نشد.")


async def set_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    blocked = update.message.text.lower().split()[0].endswith("block") and not update.message.text.lower().split()[0].endswith("unblock")
    async with async_session_factory() as s:
        user = (await s.execute(select(User).where(User.telegram_id == int(context.args[0])))).scalar_one_or_none()
        if user: user.is_blocked = blocked; await s.commit()
    await update.message.reply_text("✅ وضعیت کاربر تغییر کرد." if user else "کاربر پیدا نشد.")


async def create_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 3: return
    try:
        code, kind, value = context.args[:3]; value = int(value); limit = int(context.args[3]) if len(context.args) > 3 else None
    except ValueError: await update.message.reply_text("فرمت: /coupon کد percent|amount مقدار [سقف]"); return
    async with async_session_factory() as s: s.add(Coupon(code=code.upper(), discount_percent=value if kind == "percent" else None, discount_amount=value if kind == "amount" else None, usage_limit=limit)); await s.commit()
    await update.message.reply_text("✅ کوپن ساخته شد.")


async def wallet_adjust(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 2: return
    try: telegram_id, amount = int(context.args[0]), int(context.args[1])
    except ValueError: await update.message.reply_text("فرمت: /walletadd شناسه_تلگرام مبلغ"); return
    async with async_session_factory() as s:
        user = (await s.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
        if user: user.wallet_balance += amount; s.add(WalletTransaction(user_id=user.id, amount=amount, transaction_type="credit", description="شارژ توسط مدیر")); await s.commit()
    await update.message.reply_text("✅ کیف پول شارژ شد." if user else "کاربر پیدا نشد.")


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args: return
    async with async_session_factory() as s: users = (await s.execute(select(User).where(User.is_blocked.is_(False)))).scalars().all()
    sent = 0
    for user in users:
        try: await context.bot.send_message(user.telegram_id, " ".join(context.args)); sent += 1
        except Exception: logger.exception("Broadcast failed for %s", user.telegram_id)
    await update.message.reply_text(f"📢 پیام برای {sent} کاربر ارسال شد.")
