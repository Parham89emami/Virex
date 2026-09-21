from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import get_main_menu_keyboard, get_payment_keyboard
from database.database import async_session_factory
from database.models import Product
from services.order import active_products, create_order, debit_wallet, user_orders
from services.payment import PaymentService


async def show_plans(update, context):
    if not update.message or not update.effective_user:
        return
    async with async_session_factory() as session:
        products = await active_products(session)
    if not products:
        await update.message.reply_text("در حال حاضر محصولی موجود نیست.", reply_markup=get_main_menu_keyboard())
        return
    buttons = [[InlineKeyboardButton(f"{p.volume_gb}GB | {p.duration_days} روز | {p.price:,} تومان", callback_data=f"product:{p.id}")] for p in products]
    await update.message.reply_text("📦 محصول موردنظر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(buttons))


async def select_plan(update, context):
    query = update.callback_query
    if not query or not update.effective_user:
        return
    await query.answer()
    product_id = int((query.data or "").split(":", 1)[1])
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        product = await session.get(Product, product_id)
        if user.is_blocked:
            await query.edit_message_text("🚫 حساب شما مسدود است.")
            return
        if not product or not product.is_active:
            await query.edit_message_text("❌ محصول فعال نیست.")
            return
    context.user_data["product_id"] = product_id
    await query.edit_message_text(
        f"📦 {product.volume_gb}GB | {product.duration_days} روز\n"
        f"💰 مبلغ نهایی: {product.price:,} تومان\n\n"
        "روش پرداخت را انتخاب کنید:",
        reply_markup=get_payment_keyboard(),
    )


async def payment_choice(update, context):
    query = update.callback_query
    if not query or not update.effective_user:
        return
    await query.answer()
    method = (query.data or "").split(":")[-1]
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        product = await session.get(Product, context.user_data.get("product_id"))
        if user.is_blocked or not product or not product.is_active:
            await query.edit_message_text("🚫 خرید ممکن نیست.")
            return
        amount = product.price
        if method == "wallet" and not await debit_wallet(session, user, amount, f"خرید {product.name}"):
            await query.edit_message_text("❌ موجودی کیف پول کافی نیست.")
            return
        order = await create_order(session, user, product, amount, method)
        if method == "wallet":
            order.status = order.payment_status = "pending_review"
        await session.commit()
    context.user_data.clear()
    if method == "wallet":
        await query.edit_message_text("✅ پرداخت کیف پول ثبت شد و پس از بررسی مدیر تحویل می‌شود.")
    else:
        await query.edit_message_text("✅ سفارش ثبت شد.\n\n" + PaymentService.payment_instructions(order.order_uid, amount))


async def my_orders(update, context):
    if not update.message or not update.effective_user:
        return
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        if user.is_blocked:
            await update.message.reply_text("🚫 حساب شما مسدود است.")
            return
        orders = await user_orders(session, update.effective_user.id)
    labels = {"pending": "⏳ در انتظار پرداخت", "pending_review": "🔎 در انتظار بررسی", "completed": "✅ تکمیل‌شده", "rejected": "❌ ردشده"}
    text = "📦 سفارش‌های شما:\n" + ("\n".join(f"\n🧾 {o.order_uid}\n💾 {o.traffic_gb} گیگ | {o.duration_days} روز\n💰 {o.price_toman:,} تومان\n📌 {labels.get(o.status, o.status)}" for o in orders) if orders else "هنوز سفارشی ندارید.")
    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
