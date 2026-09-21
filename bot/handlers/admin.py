from __future__ import annotations

import logging
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import settings
from database.database import async_session_factory
from database.models import Coupon, Order, Product, User, VPNConfig
from services.order import approve_and_deliver
from sqlalchemy import func, select

logger = logging.getLogger(__name__)
def is_admin(user_id: int | None) -> bool: return user_id is not None and user_id in settings.admin_ids

def denied(update: Update) -> bool:
    return not is_admin(update.effective_user.id if update.effective_user else None)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message: return
    if denied(update): await update.message.reply_text("⛔ دسترسی غیرمجاز."); return
    async with async_session_factory() as s:
        users=(await s.execute(select(func.count(User.id)))).scalar() or 0
        orders=(await s.execute(select(func.count(Order.id)))).scalar() or 0
        successful=(await s.execute(select(func.count(Order.id)).where(Order.payment_status == "approved"))).scalar() or 0
        pending=(await s.execute(select(func.count(Order.id)).where(Order.payment_status.in_(["pending", "pending_review"])))).scalar() or 0
        sales=(await s.execute(select(func.coalesce(func.sum(Order.price_toman), 0)).where(Order.payment_status == "approved"))).scalar() or 0
        available=(await s.execute(select(func.count(VPNConfig.id)).where(VPNConfig.status == "available"))).scalar() or 0
        sold=(await s.execute(select(func.count(VPNConfig.id)).where(VPNConfig.status == "sold"))).scalar() or 0
    await update.message.reply_text(f"👑 پنل مدیریت Virex\n━━━━━━━━━━━━\n👥 کاربران: {users}\n🧾 سفارش‌ها: {orders}\n✅ موفق: {successful}\n⏳ در انتظار: {pending}\n💰 مجموع فروش: {sales:,} تومان\n🔐 موجودی: {available}\n📤 فروخته‌شده: {sold}\n\nدستورات: /products /addproduct /editproduct /toggleproduct /deleteproduct /addconfig /users /user /block /unblock /coupon /broadcast")

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update): return
    if not context.args or not context.args[0].isdigit(): await update.message.reply_text("فرمت: /confirm ORDER_ID"); return
    async with async_session_factory() as s: order, config = await approve_and_deliver(s, int(context.args[0])); user = await s.get(User, order.user_id) if order and config else None
    if not order: await update.message.reply_text("❌ سفارش پیدا نشد."); return
    if not config: await update.message.reply_text("⚠️ موجودی کانفیگ این محصول صفر است؛ سفارش تأیید نشد."); return
    try: await context.bot.send_message(user.telegram_id, f"✅ پرداخت سفارش {order.order_uid} تأیید شد!\n\n🔐 کانفیگ اختصاصی شما:\n\n{config.config_text}")
    except Exception: logger.exception("Could not deliver config for order %s", order.id)
    await update.message.reply_text(f"✅ سفارش {order.order_uid} تکمیل شد.")

async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update): return
    if not context.args or not context.args[0].isdigit(): await update.message.reply_text("فرمت: /reject ORDER_ID"); return
    async with async_session_factory() as s:
        order = await s.get(Order, int(context.args[0]))
        if order: order.status = order.payment_status = "rejected"; await s.commit()
    await update.message.reply_text("❌ سفارش رد شد." if order else "❌ سفارش پیدا نشد.")

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update): return
    async with async_session_factory() as s: rows = (await s.execute(select(Product).order_by(Product.id))).scalars().all()
    await update.message.reply_text("📦 محصولات:\n" + "\n".join(f"{p.id}: {p.name} | {p.volume_gb}GB/{p.duration_days}روز | {p.price:,} | {'فعال' if p.is_active else 'غیرفعال'}" for p in rows) if rows else "محصولی وجود ندارد.")

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 4: await update.message.reply_text("فرمت: /addproduct NAME VOLUME DAYS PRICE"); return
    try: volume, days, price = map(int, context.args[-3:]); name = " ".join(context.args[:-3])
    except ValueError: await update.message.reply_text("حجم، مدت و قیمت باید عدد باشند."); return
    async with async_session_factory() as s: s.add(Product(name=name, volume_gb=volume, duration_days=days, price=price)); await s.commit()
    await update.message.reply_text("✅ محصول اضافه شد.")

async def add_config(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 2: await update.message.reply_text("فرمت: /addconfig PRODUCT_ID CONFIG_TEXT"); return
    try: product_id = int(context.args[0])
    except ValueError: await update.message.reply_text("شناسه محصول نامعتبر است."); return
    async with async_session_factory() as s: s.add(VPNConfig(product_id=product_id, config_text=" ".join(context.args[1:]))); await s.commit()
    await update.message.reply_text("✅ کانفیگ به موجودی اضافه شد.")

async def user_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): await update.message.reply_text("فرمت: /user TELEGRAM_ID"); return
    async with async_session_factory() as s:
        user = (await s.execute(select(User).where(User.telegram_id == int(context.args[0])))).scalar_one_or_none()
        count = len(user.orders) if user else 0
    await update.message.reply_text(f"👤 {user.telegram_id}\nنام کاربری: @{user.username or '-'}\nسفارش‌ها: {count}\nکیف پول: {user.wallet_balance:,}" if user else "کاربر پیدا نشد.")

async def set_block(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as s:
        user=(await s.execute(select(User).where(User.telegram_id == int(context.args[0])))).scalar_one_or_none()
        if user: user.is_blocked = context.args[0] != "" and update.message.text.split()[0].endswith("block"); await s.commit()
    await update.message.reply_text("✅ وضعیت کاربر تغییر کرد." if user else "کاربر پیدا نشد.")

async def create_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or len(context.args) < 3: await update.message.reply_text("فرمت: /coupon CODE percent|amount VALUE [LIMIT]"); return
    try: code, kind, value = context.args[:3]; value = int(value); limit = int(context.args[3]) if len(context.args) > 3 else None
    except ValueError: await update.message.reply_text("مقادیر نامعتبر است."); return
    async with async_session_factory() as s: s.add(Coupon(code=code.upper(), discount_percent=value if kind == "percent" else None, discount_amount=value if kind == "amount" else None, usage_limit=limit)); await s.commit()
    await update.message.reply_text("✅ کد تخفیف س��خته شد.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args: return
    async with async_session_factory() as s: users=(await s.execute(select(User).where(User.is_blocked.is_(False)))).scalars().all()
    sent=0
    for user in users:
        try: await context.bot.send_message(user.telegram_id, " ".join(context.args)); sent += 1
        except Exception: logger.exception("Broadcast failed for %s", user.telegram_id)
    await update.message.reply_text(f"📢 پیام برای {sent} کاربر ارسال شد.")
