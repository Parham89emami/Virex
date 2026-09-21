from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

from bot.init import register_handlers
from config.settings import settings
from database.database import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("virex")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled update error", exc_info=context.error)


def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")
    asyncio.run(init_db())
    application = ApplicationBuilder().token(settings.bot_token).build()
    application.add_error_handler(error_handler)
    register_handlers(application)
    logger.info("Virex bot is starting in polling mode")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
