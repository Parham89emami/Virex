from __future__ import annotations
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from bot.handlers.admin import admin_panel, confirm_order, reject_order
from bot.handlers.orders import my_orders, select_plan, show_plans
from bot.handlers.payments import handle_receipt
from bot.handlers.start import main_menu_router, orders_command, start, support_command

def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start)); application.add_handler(CommandHandler("orders", orders_command)); application.add_handler(CommandHandler("support", support_command)); application.add_handler(CommandHandler("admin", admin_panel)); application.add_handler(CommandHandler("confirm", confirm_order)); application.add_handler(CommandHandler("reject", reject_order))
    application.add_handler(CallbackQueryHandler(select_plan, pattern=r"^product:\d+$")); application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt)); application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router))
