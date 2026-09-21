from __future__ import annotations
from telegram import ReplyKeyboardMarkup
BUY_BUTTON="🛒 خرید VPN";ORDERS_BUTTON="📦 سفارش‌های من";WALLET_BUTTON="💰 کیف پول";SUPPORT_BUTTON="💬 پشتیبانی";BACK_BUTTON="🔙 بازگشت"
def get_main_menu_keyboard():return ReplyKeyboardMarkup([[BUY_BUTTON,ORDERS_BUTTON],[WALLET_BUTTON,SUPPORT_BUTTON],[BACK_BUTTON]],resize_keyboard=True,input_field_placeholder="انتخاب کنید")
def get_back_keyboard():return ReplyKeyboardMarkup([[BACK_BUTTON]],resize_keyboard=True)
