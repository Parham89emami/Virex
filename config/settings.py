from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def parse_admin_ids(value: str) -> list[int]:
    return [int(item.strip()) for item in value.split(",") if item.strip().isdigit()]


def normalize_database_url(value: str) -> str:
    value = value.strip()
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+asyncpg://", 1)
    if value.startswith("postgresql://") and "+asyncpg" not in value:
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    return value


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: list[int]
    database_url: str
    card_number: str
    card_owner: str
    support_contact: str
    log_level: str


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", "").strip(),
    admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "")),
    database_url=normalize_database_url(os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./virex.db")),
    card_number=os.getenv("CARD_NUMBER", "").strip(),
    card_owner=os.getenv("CARD_OWNER", "").strip(),
    support_contact=os.getenv("SUPPORT_CONTACT", "@Parham88e").strip() or "@Parham88e",
    log_level=os.getenv("LOG_LEVEL", "INFO").strip(),
)
