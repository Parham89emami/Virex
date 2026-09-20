from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.handlers.admin import admin_panel, confirm_order, reject_order, view_receipt
from bot.handlers.orders import confirm_plan, select_plan, show_plans
from bot.handlers.payments import handle_receipt
from bot.handlers.start import about_command, main_menu_callback, main_menu_router, orders_command, plans_callback, start, support_command
from bot.handlers.orders import cancel_all_callback, confirm_cancel_all, cancel_order_callback, confirm_cancel_order


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("plans", show_plans))
    application.add_handler(CommandHandler("orders", orders_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("confirm", confirm_order))
    application.add_handler(CommandHandler("reject", reject_order))
    application.add_handler(CallbackQueryHandler(confirm_plan, pattern=r"^confirm:[a-z0-9]+$"))
    application.add_handler(CallbackQueryHandler(select_plan, pattern=r"^plan:[a-z0-9]+$"))
    application.add_handler(CallbackQueryHandler(view_receipt, pattern=r"^admin:receipt:[0-9]+$"))
    application.add_handler(CallbackQueryHandler(confirm_cancel_all, pattern=r"^cancel_all:confirm$"))
    application.add_handler(CallbackQueryHandler(cancel_all_callback, pattern=r"^cancel_all:(?:yes|no)$"))
    application.add_handler(CallbackQueryHandler(confirm_cancel_order, pattern=r"^cancel:confirm:[0-9]+$"))
    application.add_handler(CallbackQueryHandler(cancel_order_callback, pattern=r"^cancel:(?:yes|no):[0-9]+$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern=r"^menu:main$"))
    application.add_handler(CallbackQueryHandler(plans_callback, pattern=r"^menu:plans$"))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router))
