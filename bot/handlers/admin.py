from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.main import inline_menu
from config.settings import settings
from database.database import async_session_factory
from database.models import Order, Product, User, VPNConfig, WalletTransaction
from services.order import approve_and_deliver

logger = logging.getLogger(__name__)


def is_admin(user_id: int | None) -> bool:
    return user_id is not None and user_id in settings.admin_ids


def denied(update: Update) -> bool:
    return not is_admin(update.effective_user.id if update.effective_user else None)


def admin_keyboard() -> InlineKeyboardMarkup:
    return inline_menu([
        [("📦 مدیریت محصولات", "admin:products"), ("🔐 مدیریت کانفیگ‌ها", "admin:configs")],
        [("🧾 مدیریت سفارش‌ها", "admin:orders"), ("👥 مدیریت کاربران", "admin:users")],
        [("💰 مدیریت کیف پول", "admin:wallet"), ("📊 گزارش‌ها", "admin:reports")],
        [("🛟 پشتیبانی", "admin:support"), ("🔙 بازگشت", "admin:back")],
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if denied(update):
        if update.callback_query: await update.callback_query.answer("دسترسی غیرمجاز", show_alert=True)
        elif update.message: await update.message.reply_text("⛔ دسترسی غیرمجاز.")
        return
    text = "⚙️ پنل مدیریت Virex\n\nبخش موردنظر را انتخاب کنید:"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=admin_keyboard())
    elif update.message:
        await update.message.reply_text(text, reply_markup=admin_keyboard())


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not is_admin(update.effective_user.id if update.effective_user else None):
        if query: await query.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await query.answer()
    action = (query.data or "").split(":", 1)[1]
    if action == "back":
        await query.edit_message_text("منوی اصلی Virex را از دکمه‌های پایین انتخاب کنید.")
    elif action == "products":
        await query.edit_message_text("📦 مدیریت محصولات", reply_markup=inline_menu([[('➕ افزودن محصول', 'admin:help:addproduct'), ('✏️ ویرایش محصول', 'admin:help:editproduct')], [('🔴/🟢 فعال/غیرفعال', 'admin:help:toggleproduct'), ('🗑 حذف محصول', 'admin:list:deleteproduct')], [('🔙 بازگشت', 'admin:menu')]]))
    elif action == "configs":
        await query.edit_message_text("🔐 مدیریت کانفیگ‌ها", reply_markup=inline_menu([[('➕ افزودن کانفیگ', 'admin:help:addconfig'), ('📋 موجودی کانفیگ‌ها', 'admin:list:configs')], [('✅ کانفیگ‌های موجود', 'admin:list:available'), ('🔴 کانفیگ‌های فروخته‌شده', 'admin:list:sold')], [('🗑 حذف کانفیگ', 'admin:list:deleteconfig'), ('🔙 بازگشت', 'admin:menu')]]))
    elif action == "orders":
        await query.edit_message_text("🧾 مدیریت سفارش‌ها", reply_markup=inline_menu([[('📋 سفارش‌های در انتظار', 'admin:list:pending')], [('✅ تأیید سفارش', 'admin:help:confirm'), ('❌ رد سفارش', 'admin:help:reject')], [('🔎 مشاهده جزئیات سفارش', 'admin:help:order'), ('🔙 بازگشت', 'admin:menu')]]))
    elif action == "users":
        await query.edit_message_text("👥 مدیریت کاربران", reply_markup=inline_menu([[('🔎 جستجوی کاربر', 'admin:help:user'), ('🚫 مسدود کردن', 'admin:help:block')], [('✅ رفع مسدودی', 'admin:help:unblock'), ('💰 موجودی کیف پول', 'admin:help:user')], [('🔙 بازگشت', 'admin:menu')]]))
    elif action == "wallet":
        await query.edit_message_text("💰 مدیریت کیف پول", reply_markup=inline_menu([[('➕ افزایش موجودی', 'admin:help:walletadd'), ('➖ کاهش موجودی', 'admin:help:walletsub')], [('📋 تراکنش‌های کیف پول', 'admin:list:wallet'), ('🔙 بازگشت', 'admin:menu')]]))
    elif action == "reports":
        await send_reports(query)
    elif action == "support":
        await query.edit_message_text("🛟 پشتیبانی Virex\n\n👤 @Parham88e", reply_markup=inline_menu([[('🔙 بازگشت', 'admin:menu')]]))
    elif action == "menu":
        await query.edit_message_text("⚙️ پنل مدیریت Virex\n\nبخش موردنظر را انتخاب کنید:", reply_markup=admin_keyboard())
    elif action.startswith("help:"):
        command = action.split(":", 1)[1]
        messages = {'addproduct':'/addproduct نام حجم مدت قیمت', 'editproduct':'/editproduct شناسه حجم مدت قیمت', 'toggleproduct':'/toggleproduct شناسه', 'addconfig':'/addconfig شناسه_محصول متن_کانفیگ', 'confirm':'/confirm شناسه_داخلی', 'reject':'/reject شناسه_داخلی', 'order':'/order شناسه_داخلی', 'user':'/user شناسه_تلگرام', 'block':'/block شناسه_تلگرام', 'unblock':'/unblock شناسه_تلگرام', 'walletadd':'/walletadd شناسه_تلگرام مبلغ', 'walletsub':'/walletadd شناسه_تلگرام مبلغ_منفی'}
        await query.edit_message_text(f"برای انجام عملیات، دستور زیر را ارسال کنید:\n\n{messages.get(command, 'دستور نامعتبر است.')}", reply_markup=inline_menu([[('🔙 بازگشت', 'admin:menu')]]))
    elif action.startswith("list:"):
        await admin_list(query, action.split(":", 1)[1])
    elif action.startswith("delete:"):
        await delete_confirmation(query, action)
    elif action.startswith("confirmdelete:"):
        await confirm_delete(query, action)


async def send_reports(query) -> None:
    now = datetime.now(timezone.utc)
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_month = start_day.replace(day=1)
    async with async_session_factory() as session:
        today = (await session.execute(select(func.coalesce(func.sum(Order.price_toman), 0)).where(Order.status == 'completed', Order.completed_at >= start_day))).scalar() or 0
        month = (await session.execute(select(func.coalesce(func.sum(Order.price_toman), 0)).where(Order.status == 'completed', Order.completed_at >= start_month))).scalar() or 0
        total = (await session.execute(select(func.coalesce(func.sum(Order.price_toman), 0)).where(Order.status == 'completed'))).scalar() or 0
        orders = (await session.execute(select(func.count(Order.id)))).scalar() or 0
        users = (await session.execute(select(func.count(User.id)))).scalar() or 0
    await query.edit_message_text(f"📊 گزارش‌های Virex\n\n📈 فروش امروز: {today:,} تومان\n📊 فروش این ماه: {month:,} تومان\n💰 مجموع فروش: {total:,} تومان\n📦 تعداد سفارش‌ها: {orders}\n👥 تعداد کاربران: {users}", reply_markup=inline_menu([[('🔙 بازگشت', 'admin:menu')]]))


async def admin_list(query, kind: str) -> None:
    async with async_session_factory() as session:
        if kind == 'pending':
            rows = (await session.execute(select(Order).where(Order.status == 'pending_review').order_by(Order.created_at.desc()).limit(30))).scalars().all()
            text = '📋 سفارش‌��ای در انتظار\n\n' + ('\n'.join(f'#{o.id} | {o.order_uid} | {o.price_toman:,} تومان' for o in rows) if rows else 'موردی وجود ندارد.')
        elif kind in {'configs', 'available', 'sold'}:
            query_stmt = select(VPNConfig).order_by(VPNConfig.id)
            if kind != 'configs': query_stmt = query_stmt.where(VPNConfig.status == kind)
            rows = (await session.execute(query_stmt.limit(50))).scalars().all()
            text = '🔐 موجودی کانفیگ‌ها\n\n' + ('\n'.join(f'#{c.id} | محصول {c.product_id} | {c.status}' for c in rows) if rows else 'موردی وجود ندارد.')
        elif kind == 'deleteproduct':
            rows = (await session.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.id))).scalars().all()
            await query.edit_message_text('🗑 حذف محصول: مورد را انتخاب کنید', reply_markup=inline_menu([[(f'محصول #{p.id} - {p.volume_gb}GB', f'admin:delete:product:{p.id}')] for p in rows] + [[('🔙 بازگشت', 'admin:products')]])); return
        elif kind == 'deleteconfig':
            rows = (await session.execute(select(VPNConfig).where(VPNConfig.status == 'available').order_by(VPNConfig.id))).scalars().all()
            await query.edit_message_text('🗑 حذف کانفیگ: مورد را انتخاب کنید', reply_markup=inline_menu([[(f'کانفیگ #{c.id} - محصول {c.product_id}', f'admin:delete:config:{c.id}')] for c in rows] + [[('🔙 بازگشت', 'admin:configs')]])); return
        elif kind == 'wallet':
            rows = (await session.execute(select(WalletTransaction).order_by(WalletTransaction.created_at.desc()).limit(30))).scalars().all()
            text = '📋 تراکنش‌های کیف پول\n\n' + ('\n'.join(f'کاربر {r.user_id} | {r.amount:+,} | {r.transaction_type}' for r in rows) if rows else 'موردی وجود ندارد.')
        else: text = 'موردی وجود ندارد.'
    await query.edit_message_text(text, reply_markup=inline_menu([[('🔙 بازگشت', 'admin:menu')]]))


async def delete_confirmation(query, action: str) -> None:
    kind, item_id = action.split(':')[1:]
    await query.edit_message_text('⚠️ حذف این مورد قطعی است؟ این عملیات قابل بازگشت نیست.', reply_markup=inline_menu([[('✅ بله، حذف شود', f'admin:confirmdelete:{kind}:{item_id}'), ('❌ انصراف', 'admin:menu')]]))


async def confirm_delete(query, action: str) -> None:
    kind, item_id = action.split(':')[1:]
    async with async_session_factory() as session:
        model = Product if kind == 'product' else VPNConfig
        item = await session.get(model, int(item_id))
        if not item or (kind == 'config' and item.status != 'available'):
            await query.edit_message_text('❌ مورد پیدا نشد یا قابل حذف نیست.', reply_markup=inline_menu([[('🔙 بازگشت', 'admin:menu')]])); return
        if kind == 'product': item.is_active = False
        else: await session.delete(item)
        await session.commit()
    await query.edit_message_text('✅ عملیات حذف با موفقیت انجام شد.', reply_markup=inline_menu([[('🔙 بازگشت', 'admin:menu')]]))


# Legacy command handlers remain guarded and reuse the existing atomic delivery service.
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or denied(update) or not context.args or not context.args[0].isdigit(): return
    async with async_session_factory() as session:
        order, config = await approve_and_deliver(session, int(context.args[0]))
        user = await session.get(User, order.user_id) if order and config else None
    if not order: await update.message.reply_text('❌ سفارش پیدا نشد.'); return
    if not config: await update.message.reply_text('⚠️ کانفیگ available وجود ندارد؛ سفارش تکمیل نشد.'); return
    try: await context.bot.send_message(user.telegram_id, f'✅ پرداخت سفارش {order.order_uid} تأیید شد!\n\n🔐 کانفیگ Virex شما:\n{config.config_text}')
    except Exception: logger.exception('Delivery failed for order %s', order.id)
    await update.message.reply_text('✅ سفارش تأیید و کانفیگ ارسال شد.')


async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await admin_panel(update, context)
