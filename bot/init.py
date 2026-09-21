from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.handlers.admin import add_config, add_product, admin_panel, broadcast, confirm_order, configs, delete_config, delete_product, edit_product, products, reject_order, set_block, toggle_product, user_action, wallet_adjust
from bot.handlers.orders import my_orders, payment_choice, select_plan, show_plans
from bot.handlers.payments import handle_receipt
from bot.handlers.start import main_menu_router, orders_command, start, support_command
from bot.handlers.wallet import wallet


def register_handlers(application: Application) -> None:
    commands = {
        "start": start, "orders": orders_command, "support": support_command, "wallet": wallet,
        "admin": admin_panel, "confirm": confirm_order, "reject": reject_order,
        "products": products, "addproduct": add_product, "editproduct": edit_product,
        "toggleproduct": toggle_product, "deleteproduct": delete_product, "addconfig": add_config,
        "configs": configs, "deleteconfig": delete_config, "user": user_action,
        "users": user_action, "block": set_block, "unblock": set_block,
        "walletadd": wallet_adjust, "broadcast": broadcast,
    }
    for name, handler in commands.items():
        application.add_handler(CommandHandler(name, handler))
    application.add_handler(CallbackQueryHandler(select_plan, pattern=r"^product:\d+$"))
    application.add_handler(CallbackQueryHandler(payment_choice, pattern=r"^pay:(card|wallet)$"))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router))
