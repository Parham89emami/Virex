from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from bot.handlers.users import ensure_user_registered
from bot.keyboards.main import BACK_BUTTON, get_main_menu_keyboard
from database.database import async_session_factory
from services.order import active_products, create_order_for_user, get_all_orders_for_user
from database.models import User
from sqlalchemy import select
from services.payment import PaymentService

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user: return
    async with async_session_factory() as session: products = await active_products(session)
    if not products:
        await update.message.reply_text("⚠️ در حال حاضر محصول فعالی برای فروش وجود ندارد.", reply_markup=get_main_menu_keyboard()); return
    buttons = [[InlineKeyboardButton(f"{p.volume_gb} گیگ | {p.duration_days} روز | {p.price:,} تومان", callback_data=f"product:{p.id}")] for p in products]
    await update.message.reply_text("📦 محصول موردنظر را انتخاب کنید:\n\nتمام قیمت‌ها از پنل مدیریت قابل تغییر است.", reply_markup=InlineKeyboardMarkup(buttons))

async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not update.effective_user: return
    await query.answer()
    try: product_id = int((query.data or "").split(":", 1)[1])
    except (ValueError, IndexError): return
    async with async_session_factory() as session:
        user = await ensure_user_registered(session, update.effective_user)
        if user.is_blocked: await query.edit_message_text("🚫 حساب شما مسدود است."); return
        from database.models import Product
        product = (await session.execute(select(Product).where(Product.id == product_id, Product.is_active.is_(True)))).scalar_one_or_none()
        if not product: await query.edit_message_text("❌ محصول معتبر نیست."); return
        order = await create_order_for_user(session, user, product)
    await query.edit_message_text("✅ سفارش ثبت شد.\n\n" + PaymentService().payment_instructions(order.order_uid, order.price_toman), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(BACK_BUTTON, callback_data="menu_main")]]))

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user: return
    async with async_session_factory() as session: orders = await get_all_orders_for_user(session, update.effective_user.id)
    if not orders: await update.message.reply_text("📦 هنوز سفارشی ندارید.", reply_markup=get_main_menu_keyboard()); return
    labels = {"pending":"⏳ در انتظار پرداخت", "pending_review":"🔎 در انتظار بررسی", "completed":"✅ تکمیل‌شده", "rejected":"❌ ردشده"}
    lines = ["📦 سفارش‌های شما:"]
    for o in orders: lines.append(f"\n━━━━━━━━━━━━\n🧾 {o.order_uid}\n💾 {o.traffic_gb} گیگ | {o.duration_days} روز\n💰 {o.price_toman:,} تومان\n📌 {labels.get(o.status, o.status)}")
    await update.message.reply_text("\n".join(lines), reply_markup=get_main_menu_keyboard())
