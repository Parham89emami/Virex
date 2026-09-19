from telegram import ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["🛒 خرید VPN", "📦 سفارش‌های من"]],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
