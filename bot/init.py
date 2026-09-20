from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.handlers.admin import admin_panel, confirm_order, reject_order
from bot.handlers.orders import confirm_plan, select_plan, show_plans
from bot.handlers.payments import handle_receipt
from bot.handlers.start import (
    about_command,
    main_menu_callback,
    main_menu_router,
    orders_command,
    plans_callback,
    start,
    support_command,
)


def register_handlers(application: Application) -> None:
    """Register commands first, then specific callbacks and text/media handlers."""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("plans", show_plans))
    application.add_handler(CommandHandler("orders", orders_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("confirm", confirm_order))
    application.add_handler(CommandHandler("reject", reject_order))

    application.add_handler(CallbackQueryHandler(confirm_plan, pattern=r"^confirm:[a-z0-9]+$"))
    application.add_handler(CallbackQueryHandler(select_plan, pattern=r"^plan:[a-z0-9]+$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern=r"^menu:main$"))
    application.add_handler(CallbackQueryHandler(plans_callback, pattern=r"^menu:plans$"))

    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router))
