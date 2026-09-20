from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler

from bot.handlers.orders import cancel_all_callback, confirm_cancel_all


def register_order_cancel_handlers(application: Application) -> None:
    application.add_handler(CallbackQueryHandler(confirm_cancel_all, pattern=r"^cancel_all:confirm$"))
    application.add_handler(CallbackQueryHandler(cancel_all_callback, pattern=r"^cancel_all:(?:yes|no)$"))
