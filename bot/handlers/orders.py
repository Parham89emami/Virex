from __future__ import annotations
import logging
from telegram import InlineKeyboardButton,InlineKeyboardMarkup,Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import BACK_BUTTON,get_main_menu_keyboard
from database.database import async_session_factory
from database.models import Product
from services.order import active_products,coupon_price,create_order,debit_wallet,user_orders
from services.payment import PaymentService
logger=logging.getLogger(__name__)
async def show_plans(update,context):
    if not update.message or not update.effective_user:return
    async with async_session_factory() as s:ps=await active_products(s)
    buttons=[[InlineKeyboardButton(f"{p.volume_gb} گیگ | {p.duration_days} روز | {p.price:,} تومان",callback_data=f"product:{p.id}")] for p in ps]
    await update.message.reply_text("📦 محصول موردنظر را انتخاب کنید:",reply_markup=InlineKeyboardMarkup(buttons) if buttons else get_main_menu_keyboard())
async def select_plan(update,context):
    q=update.callback_query
    if not q or not update.effective_user:return
    await q.answer()
    try:pid=int((q.data or "").split(":",1)[1])
    except (ValueError,IndexError):await q.edit_message_text("❌ محصول نامعتبر است.");return
    async with async_session_factory() as s:
        u=await ensure_user_registered(s,update.effective_user);p=await s.get(Product,pid)
        if u.is_blocked:await q.edit_message_text("🚫 حساب شما مسدود است.");return
        if not p or not p.is_active:await q.edit_message_text("❌ محصول فعال نیست.");return
    context.user_data["product_id"]=pid;await q.edit_message_text("🎟 کد تخفیف را بفرستید یا «ندارم» را ارسال کنید.")
async def handle_coupon_input(update,context):
    if "product_id" not in context.user_data:
        from bot.handlers.start import main_menu_router
        await main_menu_router(update,context);return
    if not update.message or not update.effective_user:return
    code=update.message.text.strip()
    async with async_session_factory() as s:
        u=await ensure_user_registered(s,update.effective_user);p=await s.get(Product,context.user_data["product_id"])
        if u.is_blocked:await update.message.reply_text("🚫 حساب شما مسدود است.");return
        if not p or not p.is_active:await update.message.reply_text("❌ محصول فعال نیست.");return
        amount=p.price;coupon=None
        if code.lower() not in {"ندارم","ندارم.","none","no"}:
            amount,coupon,error=await coupon_price(s,code,u.id,p.price)
            if error:await update.message.reply_text(f"❌ {error}");return
    context.user_data["coupon"]=code if coupon else None;context.user_data["amount"]=amount
    await update.message.reply_text(f"💰 مبلغ نهایی: {amount:,} تومان",reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 کارت‌به‌کارت",callback_data="pay:card"),InlineKeyboardButton("💰 کیف پول",callback_data="pay:wallet")]]))
async def payment_choice(update,context):
    q=update.callback_query;await q.answer();method=(q.data or "").split(":")[-1]
    async with async_session_factory() as s:
        u=await ensure_user_registered(s,update.effective_user);p=await s.get(Product,context.user_data.get("product_id"))
        if u.is_blocked or not p or not p.is_active:await q.edit_message_text("🚫 خرید ممکن نیست.");return
        amount=p.price;coupon=None
        if context.user_data.get("coupon"):amount,coupon,error=await coupon_price(s,context.user_data["coupon"],u.id,p.price); 
        if method=="wallet":
            if not await debit_wallet(s,u,amount,f"خرید {p.name}"):await q.edit_message_text("❌ موجودی کیف پول کافی نیست.");return
            o=await create_order(s,u,p,amount,coupon);o.status=o.payment_status="pending_review";await s.commit();await q.edit_message_text("✅ پرداخت از کیف پول ثبت شد و پس از بررسی موجودی، کانفیگ تحویل می‌شود.")
        else:o=await create_order(s,u,p,amount,coupon);await q.edit_message_text("✅ سفارش ثبت شد.\n\n"+PaymentService().payment_instructions(o.order_uid,amount))
    context.user_data.clear()
async def my_orders(update,context):
    if not update.message or not update.effective_user:return
    async with async_session_factory() as s:
        u=await ensure_user_registered(s,update.effective_user)
        if u.is_blocked:await update.message.reply_text("🚫 حساب شما مسدود است.");return
        orders=await user_orders(s,update.effective_user.id)
    labels={"pending":"⏳ در انتظار پرداخت","pending_review":"🔎 در انتظار بررسی","completed":"✅ تکمیل‌شده","rejected":"❌ ردشده"}
    text="📦 سفارش‌های شما:\n"+("\n".join(f"\n🧾 {o.order_uid}\n💾 {o.traffic_gb} گیگ | {o.duration_days} روز\n💰 {o.price_toman:,} تومان\n📌 {labels.get(o.status,o.status)}" for o in orders) if orders else "هنوز سفارشی ندارید.")
    await update.message.reply_text(text,reply_markup=get_main_menu_keyboard())
