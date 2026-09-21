from __future__ import annotations
import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from bot.handlers.admin import admin_panel, add_config, add_product, broadcast, confirm_order, create_coupon, products, reject_order, set_block, user_action
from bot.handlers.orders import my_orders, select_plan, show_plans
from bot.handlers.payments import handle_receipt
from bot.handlers.start import main_menu_router, orders_command, start, support_command
from bot.handlers.wallet import wallet

def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start)); application.add_handler(CommandHandler("orders", orders_command)); application.add_handler(CommandHandler("support", support_command)); application.add_handler(CommandHandler("wallet", wallet)); application.add_handler(CommandHandler("admin", admin_panel)); application.add_handler(CommandHandler("confirm", confirm_order)); application.add_handler(CommandHandler("reject", reject_order)); application.add_handler(CommandHandler("products", products)); application.add_handler(CommandHandler("addproduct", add_product)); application.add_handler(CommandHandler("addconfig", add_config)); application.add_handler(CommandHandler("user", user_action)); application.add_handler(CommandHandler("users", user_action)); application.add_handler(CommandHandler("block", set_block)); application.add_handler(CommandHandler("unblock", set_block)); application.add_handler(CommandHandler("coupon", create_coupon)); application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(select_plan, pattern=r"^product:\d+$")); application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_receipt)); application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router))
