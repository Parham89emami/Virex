from __future__ import annotations

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.keyboards.main import get_main_menu_keyboard, get_wallet_keyboard
from config.settings import settings
from database.database import async_session_factory
from services.order import (
    get_or_create_user,
    create_wallet_topup_request,
    update_wallet_topup_receipt,
    get_topup_request_by_id,
)

logger = logging.getLogger(__name__)

WAITING_FOR_TOPUP_AMOUNT = 1


async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display wallet balance and topup button."""
    if not update.message or not update.effective_user:
        return

    async with async_session_factory() as session:
        user = await get_or_create_user(session, update.effective_user)
        if user.is_blocked:
            await update.message.reply_text("🚫 حساب شما مسدود است.")
            return
        balance = user.wallet_balance

    await update.message.reply_text(
        f"💰 موجودی کیف پول Virex: {balance:,} تومان\n\nاز دکمه زیر برای شارژ کیف پول استفاده کنید:",
        reply_markup=get_wallet_keyboard(),
    )


async def start_topup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start wallet topup process."""
    query = update.callback_query
    if not query or not update.effective_user:
        return ConversationHandler.END

    await query.answer()
    await query.edit_message_text(
        "🔢 لطفاً مبلغ شارژ را به تومان وارد کنید:\n\n(مثلاً: 100000)",
    )
    return WAITING_FOR_TOPUP_AMOUNT


async def handle_topup_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Validate and process topup amount."""
    if not update.message or not update.message.text or not update.effective_user:
        return ConversationHandler.END

    amount_text = update.message.text.strip()

    try:
        amount = int(amount_text)
    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ باید یک عدد صحیح باشد. دوبا��ه سعی کنید:",
        )
        return WAITING_FOR_TOPUP_AMOUNT

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد. دوباره سعی کنید:",
        )
        return WAITING_FOR_TOPUP_AMOUNT

    if amount > 50_000_000:
        await update.message.reply_text(
            "❌ مبلغ بیش از حد مجاز است (حداکثر ۵۰ میلیون تومان). دوباره سعی کنید:",
        )
        return WAITING_FOR_TOPUP_AMOUNT

    context.user_data["topup_amount"] = amount

    card_number = settings.wallet_card_number
    card_owner = settings.wallet_card_owner

    await update.message.reply_text(
        f"💳 اطلاعات پرداخت کارت‌به‌کارت:\n\n"
        f"شماره کارت: {card_number}\n"
        f"نام صاحب کارت: {card_owner}\n"
        f"مبلغ: {amount:,} تومان\n\n"
        f"✅ مبلغ فوق‌الذکر را کارت‌به‌کارت کنید.\n"
        f"📸 سپس عکس یا فایل رسید پرداخت را اینجا ارسال کنید.\n\n"
        f"⏱ منتظر رسید خود باشید...",
    )

    async with async_session_factory() as session:
        user = await get_or_create_user(session, update.effective_user)
        topup_request = await create_wallet_topup_request(session, user, amount)
        context.user_data["topup_request_id"] = topup_request.id

    return ConversationHandler.END


async def handle_topup_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle receipt upload for topup."""
    if not update.message or not update.effective_user:
        return

    topup_request_id = context.user_data.get("topup_request_id")
    if not topup_request_id:
        await update.message.reply_text(
            "❌ درخواست شارژ پیدا نشد. لطفاً دوباره شروع کنید.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        file_name = "receipt.jpg"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_name = update.message.document.file_name or "receipt"
    else:
        await update.message.reply_text(
            "❌ لطفاً عکس یا فایل رسید ارسال کنید.",
        )
        return

    async with async_session_factory() as session:
        topup_request = await get_topup_request_by_id(session, topup_request_id)
        if not topup_request:
            await update.message.reply_text(
                "❌ درخواست شارژ پیدا نشد.",
                reply_markup=get_main_menu_keyboard(),
            )
            return

        await update_wallet_topup_receipt(session, topup_request, file_id, file_name)

    await update.message.reply_text(
        "✅ رسید دریافت شد و برای بررسی ادمین ارسال شد.\n"
        "⏱ پس از تأیید، موجودی کیف پول شما افزایش می‌یابد.\n\n"
        "بازگشت به منو:",
        reply_markup=get_main_menu_keyboard(),
    )

    context.user_data.pop("topup_request_id", None)
    context.user_data.pop("topup_amount", None)

    await send_receipt_to_admin(update, topup_request_id)


async def send_receipt_to_admin(update: Update, topup_request_id: int) -> None:
    """Send receipt to admin for approval."""
    async with async_session_factory() as session:
        topup_request = await get_topup_request_by_id(session, topup_request_id)
        if not topup_request or not topup_request.receipt_file_id:
            return

        user = await session.get(User, topup_request.user_id) if topup_request else None

    for admin_id in settings.admin_ids:
        try:
            approve_button = InlineKeyboardButton(
                "✅ تأیید شارژ",
                callback_data=f"wallet_topup_approve:{topup_request_id}",
            )
            reject_button = InlineKeyboardButton(
                "❌ رد شارژ",
                callback_data=f"wallet_topup_reject:{topup_request_id}",
            )
            keyboard = InlineKeyboardMarkup([[approve_button, reject_button]])

            message_text = (
                f"💰 درخواست شارژ کیف پول\n\n"
                f"🆔 شناسه: {topup_request.request_uid}\n"
                f"👤 کاربر: {user.telegram_id if user else 'نامشخص'}\n"
                f"🏷 نام: {user.first_name or ''} {user.last_name or ''}".strip() + "\n"
                f"💵 مبلغ: {topup_request.amount_toman:,} تومان\n\n"
                f"📸 رسید: {topup_request.receipt_file_name}"
            )

            await update.get_bot().send_document(
                chat_id=admin_id,
                document=topup_request.receipt_file_id,
                caption=message_text,
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.exception("Failed to send topup receipt to admin %d: %s", admin_id, e)


from database.models import User
