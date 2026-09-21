from __future__ import annotations
import logging
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import func, select
from config.settings import settings
from database.database import async_session_factory
from database.models import Coupon, Order, Product, User, VPNConfig
from services.order import approve_and_deliver
logger=logging.getLogger(__name__)
def is_admin(uid:int|None)->bool:return uid is not None and uid in settings.admin_ids
def denied(update:Update)->bool:return not is_admin(update.effective_user.id if update.effective_user else None)
async def admin_panel(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message:return
    if denied(update):await update.message.reply_text("⛔ دسترسی غیرمجاز.");return
    async with async_session_factory() as s:
        vals=[]
        for q in (select(func.count(User.id)),select(func.count(Order.id)),select(func.count(Order.id)).where(Order.payment_status=="approved"),select(func.count(Order.id)).where(Order.payment_status.in_(["pending","pending_review"])),select(func.coalesce(func.sum(Order.price_toman),0)).where(Order.payment_status=="approved"),select(func.count(VPNConfig.id)).where(VPNConfig.status=="available"),select(func.count(VPNConfig.id)).where(VPNConfig.status=="sold")):vals.append((await s.execute(q)).scalar() or 0)
    await update.message.reply_text(f"👑 پنل مدیریت Virex\n👥 کاربران: {vals[0]}\n🧾 سفارش‌ها: {vals[1]}\n✅ موفق: {vals[2]}\n⏳ در انتظار: {vals[3]}\n💰 فروش کل: {vals[4]:,}\n🔐 موجودی: {vals[5]}\n📤 فروخته‌شده: {vals[6]}\nدستورات: /products /addproduct /editproduct /toggleproduct /deleteproduct /addconfig /configs /deleteconfig /user /block /unblock /coupon /broadcast")
async def confirm_order(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit():return
    async with async_session_factory() as s:order,config=await approve_and_deliver(s,int(context.args[0]));user=await s.get(User,order.user_id) if order and config else None
    if not order:await update.message.reply_text("❌ سفارش پیدا نشد.");return
    if not config:await update.message.reply_text("⚠️ موجودی کانفیگ صفر است؛ سفارش تکمیل نشد.");return
    try:await context.bot.send_message(user.telegram_id,f"✅ پرداخت سفارش {order.order_uid} تأیید شد!\n\n🔐 کانفیگ شما:\n{config.config_text}")
    except Exception:logger.exception("delivery failed")
    await update.message.reply_text(f"✅ سفارش {order.order_uid} تکمیل شد.")
async def reject_order(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit():return
    async with async_session_factory() as s:o=await s.get(Order,int(context.args[0]));o.status=o.payment_status="rejected";await s.commit() if o else s.rollback()
    await update.message.reply_text("❌ سفارش رد شد." if o else "❌ سفارش پیدا نشد.")
async def products(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update):return
    async with async_session_factory() as s: rows=(await s.execute(select(Product).order_by(Product.id))).scalars().all()
    await update.message.reply_text("📦 محصولات:\n"+"\n".join(f"{p.id}: {p.name} | {p.volume_gb}GB/{p.duration_days}روز | {p.price:,} | {'فعال' if p.is_active else 'غیرفعال'}" for p in rows))
async def add_product(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or len(context.args)<4:return
    try:v,d,p=map(int,context.args[-3:]);n=" ".join(context.args[:-3])
    except ValueError:await update.message.reply_text("مقادیر عددی نامعتبر است.");return
    async with async_session_factory() as s:s.add(Product(name=n,volume_gb=v,duration_days=d,price=p));await s.commit()
    await update.message.reply_text("✅ محصول اضافه شد.")
async def add_config(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or len(context.args)<2:return
    try:pid=int(context.args[0])
    except ValueError:return
    async with async_session_factory() as s:s.add(VPNConfig(product_id=pid,config_text=" ".join(context.args[1:])));await s.commit()
    await update.message.reply_text("✅ کانفیگ اضافه شد.")
async def configs(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update):return
    async with async_session_factory() as s:rows=(await s.execute(select(VPNConfig).order_by(VPNConfig.id))).scalars().all()
    await update.message.reply_text("🔐 موجودی:\n"+"\n".join(f"{x.id}: محصول {x.product_id} | {x.status}" for x in rows) if rows else "موجودی خالی است.")
async def user_action(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit():return
    async with async_session_factory() as s:u=(await s.execute(select(User).where(User.telegram_id==int(context.args[0])))).scalar_one_or_none();count=(await s.execute(select(func.count(Order.id)).where(Order.user_id==u.id))).scalar() if u else 0
    await update.message.reply_text(f"👤 {u.telegram_id}\nسفارش‌ها: {count}\nکیف پول: {u.wallet_balance:,}\nمسدود: {'بله' if u.is_blocked else 'خیر'}" if u else "کاربر پیدا نشد.")
async def set_block(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit():return
    blocked=update.message.text.split()[0].lower().endswith("block") and not update.message.text.split()[0].lower().endswith("unblock")
    async with async_session_factory() as s:u=(await s.execute(select(User).where(User.telegram_id==int(context.args[0])))).scalar_one_or_none();u.is_blocked=blocked;await s.commit() if u else s.rollback()
    await update.message.reply_text("✅ وضعیت کاربر تغییر کرد." if u else "کاربر پیدا نشد.")
async def create_coupon(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or len(context.args)<3:return
    try:code,kind,val=context.args[:3];val=int(val);limit=int(context.args[3]) if len(context.args)>3 else None
    except ValueError:return
    async with async_session_factory() as s:s.add(Coupon(code=code.upper(),discount_percent=val if kind=="percent" else None,discount_amount=val if kind=="amount" else None,usage_limit=limit));await s.commit()
    await update.message.reply_text("✅ کد تخفیف ساخته شد.")
async def broadcast(update:Update,context:ContextTypes.DEFAULT_TYPE)->None:
    if not update.message or denied(update) or not context.args:return
    async with async_session_factory() as s:users=(await s.execute(select(User).where(User.is_blocked.is_(False)))).scalars().all()
    sent=0
    for u in users:
        try:await context.bot.send_message(u.telegram_id," ".join(context.args));sent+=1
        except Exception:logger.exception("broadcast failed")
    await update.message.reply_text(f"📢 پیام برای {sent} کاربر ارسال شد.")
