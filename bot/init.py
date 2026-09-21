from __future__ import annotations
from telegram.ext import Application,CallbackQueryHandler,CommandHandler,MessageHandler,filters
from bot.handlers.admin import admin_panel,add_config,add_product,broadcast,confirm_order,create_coupon,products,reject_order,set_block,user_action,configs
from bot.handlers.orders import handle_coupon_input,my_orders,payment_choice,select_plan,show_plans
from bot.handlers.payments import handle_receipt
from bot.handlers.start import main_menu_router,orders_command,start,support_command
from bot.handlers.wallet import wallet
def register_handlers(application:Application)->None:
    handlers={"start":start,"orders":orders_command,"support":support_command,"wallet":wallet,"admin":admin_panel,"confirm":confirm_order,"reject":reject_order,"products":products,"addproduct":add_product,"addconfig":add_config,"configs":configs,"user":user_action,"users":user_action,"block":set_block,"unblock":set_block,"coupon":create_coupon,"broadcast":broadcast}
    for name,handler in handlers.items():application.add_handler(CommandHandler(name,handler))
    application.add_handler(CallbackQueryHandler(select_plan,pattern=r"^product:\d+$"));application.add_handler(CallbackQueryHandler(payment_choice,pattern=r"^pay:(card|wallet)$"));application.add_handler(MessageHandler(filters.PHOTO|filters.Document.ALL,handle_receipt));application.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,handle_coupon_input));application.add_handler(MessageHandler(filters.TEXT&~filters.COMMAND,main_menu_router))
