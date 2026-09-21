from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import get_main_menu_keyboard
from config.settings import settings
from database.database import async_session_factory
from database.models import Product
from services.order import active_products, coupon_price, create_order, debit_wallet, user_orders
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
    await query.edit_message_text("🎟 کد تخفیف را بفرستید یا «ندارم» را ارسال کنید.")


async def handle_coupon_input(update, context):
    if not update.message or not update.effective_user:
        return
    if "product_id" not in context.user_data:
        from bot.handlers.start import main_menu_router
        await main_menu_router(update, context)
        return
    code = update.message.text.strip()
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        product = await session.get(Product, context.user_data["product_id"])
        if not product or not product.is_active or user.is_blocked:
            await update.message.reply_text("🚫 خرید ممکن نیست.", reply_markup=get_main_menu_keyboard())
            context.user_data.clear()
            return
        amount, coupon, error = (product.price, None, None) if code.lower() in {"ندارم", "no", "none"} else await coupon_price(session, code, user.id, product.price)
    if error:
        await update.message.reply_text(f"❌ {error}")
        return
    context.user_data["coupon"] = code if coupon else None
    await update.message.reply_text(f"💰 مبلغ نهایی: {amount:,} تومان", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💳 کارت‌به‌کارت", callback_data="pay:card"), InlineKeyboardButton("💰 کیف پول", callback_data="pay:wallet")]]))


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
        amount, coupon, error = (product.price, None, None) if not context.user_data.get("coupon") else await coupon_price(session, context.user_data["coupon"], user.id, product.price)
        if error:
            await query.edit_message_text(f"❌ {error}")
            return
        if method == "wallet" and not await debit_wallet(session, user, amount, f"خرید {product.name}"):
            await query.edit_message_text("❌ موجودی کیف پول کافی نیست.")
            return
        order = await create_order(session, user, product, amount, coupon, method)
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
            await update.message.reply_text("🚫 حس��ب شما مسدود است.")
            return
        orders = await user_orders(session, update.effective_user.id)
    labels = {"pending": "⏳ در انتظار پرداخت", "pending_review": "🔎 در انتظار بررسی", "completed": "✅ تکمیل‌شده", "rejected": "❌ ردشده"}
    text = "📦 سفارش‌های شما:\n" + ("\n".join(f"\n🧾 {o.order_uid}\n💾 {o.traffic_gb} گیگ | {o.duration_days} روز\n💰 {o.price_toman:,} تومان\n📌 {labels.get(o.status, o.status)}" for o in orders) if orders else "هنوز سفارشی ندارید.")
    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
