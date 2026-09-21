from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.handlers.admin import admin_callback, admin_panel, admin_panel_command, confirm_order
from bot.handlers.orders import my_orders, payment_choice, select_plan, show_plans
from bot.handlers.payments import handle_receipt
from bot.handlers.start import main_menu_router, orders_command, start, support_command
from bot.handlers.wallet import wallet


def register_handlers(application: Application) -> None:
    commands = {
        'start': start, 'orders': orders_command, 'support': support_command, 'wallet': wallet,
        'admin': admin_panel_command, 'confirm': confirm_order,
    }
    for name, handler in commands.items():
        application.add_handler(CommandHandler(name, handler))
    application.add_handler(CallbackQueryHandler(select_plan, pattern=r'^product:\d+$'))
    application.add_handler(CallbackQueryHandler(payment_choice, pattern=r'^pay:(card|wallet)$'))
    application.add_handler(CallbackQueryHandler(admin_callback, pattern=r'^admin:'))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router))
