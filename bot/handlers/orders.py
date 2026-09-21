from __future__ import annotations

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import BACK_BUTTON, get_main_menu_keyboard
from database.database import async_session_factory
from database.models import Product
from services.order import active_products, calculate_coupon, charge_wallet, create_order_for_user, get_all_orders_for_user
from services.payment import PaymentService

logger = logging.getLogger(__name__)

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user: return
    async with async_session_factory() as session: products = await active_products(session)
    buttons = [[InlineKeyboardButton(f"{p.volume_gb} گیگ | {p.duration_days} روز | {p.price:,} تومان", callback_data=f"product:{p.id}")] for p in products]
    await update.message.reply_text("📦 محصول موردنظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons) if buttons else get_main_menu_keyboard())

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not update.effective_user: return
    await query.answer()
    try: product_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError): await query.edit_message_text("❌ محصول نامعتبر است."); return
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        product = (await session.execute(select(Product).where(Product.id == product_id, Product.is_active.is_(True)))).scalar_one_or_none()
        if user.is_blocked: await query.edit_message_text("🚫 حساب شما مسدود است."); return
        if not product: await query.edit_message_text("❌ محصول دیگر فعال نیست."); return
    context.user_data["pending_product_id"] = product_id
    await query.edit_message_text("🎟 اگر کد تخفیف دارید ارسال کنید؛ در غیر این صورت کلمه «ندارم» را بفرستید.")

async def handle_coupon_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or "pending_product_id" not in context.user_data: return False
    code = update.message.text.strip()
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        if user.is_blocked: await update.message.reply_text("🚫 حساب شما مسدود است."); return True
        product = await session.get(Product, context.user_data["pending_product_id"])
        if not product or not product.is_active: await update.message.reply_text("❌ محصول دیگر فعال نیست."); context.user_data.pop("pending_product_id", None); return True
        coupon = None; amount = product.price
        if code.lower() not in {"ندارم", "ندارم.", "no", "none"}:
            amount, coupon, error = await calculate_coupon(session, code, user.id, product.price)
            if error: await update.message.reply_text(f"❌ {error}"); return True
    context.user_data["pending_coupon_code"] = code if coupon else None
    context.user_data["pending_amount"] = amount
    buttons = [[InlineKeyboardButton("💳 پرداخت کارت‌به‌کارت", callback_data="pay:card"), InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data="pay:wallet")]]
    await update.message.reply_text(f"مبلغ نهایی: {amount:,} تومان\nروش پرداخت را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))
    return True

async def finalize_order(update: Update, context: ContextTypes.DEFAULT_TYPE, method: str) -> None:
    query = update.callback_query
    if not query or not update.effective_user: return
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        product_id = context.user_data.get("pending_product_id")
        product = await session.get(Product, product_id) if product_id else None
        if user.is_blocked or not product or not product.is_active: await query.edit_message_text("🚫 خرید برای این حساب/محصول ممکن نیست."); return
        amount = int(context.user_data.get("pending_amount", product.price)); coupon = None
        if context.user_data.get("pending_coupon_code"):
            amount, coupon, error = await calculate_coupon(session, context.user_data["pending_coupon_code"], user.id, product.price)
            if error: await query.edit_message_text(f"❌ {error}"); return
        if method == "wallet":
            if not await charge_wallet(session, user, amount, f"خرید {product.name}"): await query.edit_message_text("❌ موجودی کیف پول کافی نیست."); return
            order = await create_order_for_user(session, user, product, amount, coupon)
            order.payment_status = "approved"; await session.commit()
            await query.edit_message_text(f"✅ پرداخت از کیف پول انجام شد. سفارش {order.order_uid} پس از تأیید مدیر تحویل می‌شود.")
        else:
            order = await create_order_for_user(session, user, product, amount, coupon)
            await query.edit_message_text("✅ سفارش ثبت شد.\n\n" + PaymentService().payment_instructions(order.order_uid, amount))
    context.user_data.clear()

async def payment_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await finalize_order(update, context, (query.data or "").split(":")[-1])

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user: return
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        if user.is_blocked: await update.message.reply_text("🚫 حساب شما مسدود است."); return
        orders = await get_all_orders_for_user(session, update.effective_user.id)
    labels = {"pending":"⏳ در انتظار پرداخت", "pending_review":"🔎 در انتظار بررسی", "completed":"✅ تکمیل‌شده", "rejected":"❌ ردشده"}
    await update.message.reply_text("📦 سفارش‌های شما:\n" + ("\n".join(f"\n🧾 {o.order_uid}\n💾 {o.traffic_gb} گیگ | {o.duration_days} روز\n💰 {o.price_toman:,} تومان\n📌 {labels.get(o.status, o.status)}" for o in orders) if orders else "هنوز سفارشی ندارید."), reply_markup=get_main_menu_keyboard())
