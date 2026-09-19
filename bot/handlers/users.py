from __future__ import annotations

from telegram import User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.order import get_or_create_user


async def ensure_user_registered(session: AsyncSession, telegram_user: TelegramUser) -> User:
    return await get_or_create_user(session, telegram_user)
