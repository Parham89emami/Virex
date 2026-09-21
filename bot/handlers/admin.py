from __future__
from telegram import Update
from telegram.ext import ContextTypes
from config.settings import settings
from database.database import async_session_factory
from database.models import Order, User, Product, VPNConfig
from services.order import approve_and_deliver, get_pending_orders
from sqlalchemy import func, select

def is_admin(user_id: int | None) -> bool: return user_id is not None and user_id in settings.admin_ids
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message: return
    if not is_admin(update.effective_user.id if update.effective_user else None): await update.message.reply_text("⛔ دسترسی غیرمجاز."); return
    async with async_session_factory() as s:
        users=(await s.execute(select(func.count(User.id)))).scalar() or 0; orders=(await s.execute(select(func.count(Order.id)))).scalar() or 0; sales=(await s.execute(select(func.coalesce(func.sum(Order.price_toman),0)).where(Order.payment_status=="approved"))).scalar() or 0; available=(await s.execute(select(func.count(VPNConfig.id)).where(VPNConfig.status=="available"))).scalar() or 0; sold=(await s.execute(select(func.count(VPNConfig.id)).where(VPNConfig.status=="sold"))).scalar() or 0
    await update.message.reply_text(f"👑 پنل مدیریت Virex\n━━━━━━━━━━━━\n👥 کاربران: {users}\n🧾 سفارش‌ها: {orders}\n✅ فروش موفق: {sales:,} تومان\n🔐 موجودی کانفیگ: {available}\n📤 کانفیگ فروخته‌شده: {sold}\n\nدستورات: /products /addproduct /addconfig /users /user /block /unblock /broadcast")
async def _change_order(update: Update, context: ContextTypes.DEFAULT_TYPE, approved: bool) -> None:
    if not update.message or not is_admin(update.effective_user.id if update.effective_user else None): return
    if not context.args or not approved: await update.message.reply_text("فرمت: /confirm ORDER_ID" if approved else "رد سفارش با /reject ORDER_ID"); return
    try: order_id=int(context.args[0])
    except ValueError: await update.message.reply_text("شناسه باید عددی باشد."); return
    async with async_session_factory() as s:
        order, config = await approve_and_deliver(s, order_id)
        if not order: await update.message.reply_text("❌ سفارش پیدا نشد."); return
        if not config: await update.message.reply_text("⚠️ موجودی کانفیگ این محصول صفر است؛ سفارش تأیید نشد و کانفیگ تحویل نشد."); return
        user=await s.get(User, order.user_id)
    try: await context.bot.send_message(user.telegram_id, f"✅ پرداخت سفارش {order.order_uid} تأیید شد!\n\n🔐 کانفیگ اختصاصی شما:\n\n{config.config_text}")
    except Exception: pass
    await update.message.reply_text(f"✅ سفارش {order.order_uid} تکمیل و کانفیگ ارسال شد.")
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: await _change_order(update, context, True)
async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and is_admin(update.effective_user.id if update.effective_user else None) and context.args:
        async with async_session_factory() as s:
            o=await s.get(Order, int(context.args[0]));
            if o: o.status=o.payment_status="rejected"; await s.commit()
        await update.message.reply_text("❌ سفارش رد شد.")
