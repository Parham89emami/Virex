from __future__ import annotations

import asyncio

from telegram.ext import ApplicationBuilder

from bot.init import register_handlers
from config.settings import settings
from database.database import init_db


def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است. آن را در متغیرهای محیطی Railway وارد کنید.")
    asyncio.run(init_db())
    application = ApplicationBuilder().token(settings.bot_token).build()
    register_handlers(application)
    application.run_polling(allowed_updates=None, drop_pending_updates=True)


if __name__ == "__main__":
    main()
