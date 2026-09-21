from __future__ import annotations
import asyncio
import logging
from telegram.ext import ApplicationBuilder
from bot.init import register_handlers
from config.settings import settings
from database.database import init_db
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("virex")
async def error_handler(update, context) -> None:
    logger.exception("Unhandled update error", exc_info=context.error)
def main() -> None:
    if not settings.bot_token: raise RuntimeError("BOT_TOKEN تنظیم نشده است.")
    asyncio.run(init_db())
    app = ApplicationBuilder().token(settings.bot_token).build()
    app.add_error_handler(error_handler)
    register_handlers(app)
    app.run_polling(allowed_updates=None, drop_pending_updates=True)
if __name__ == "__main__": main()
