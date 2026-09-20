from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def parse_admin_ids(value: str) -> list[int]:
    ids: list[int] = []
    for item in value.split(","):
        try:
            if item.strip():
                ids.append(int(item.strip()))
        except ValueError:
            continue
    return ids


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: list[int]
    database_url: str
    card_number: str
    card_owner: str
    support_contact: str
    marzban_enabled: bool
    marzban_url: str
    marzban_username: str
    marzban_password: str


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    admin_ids=parse_admin_ids(os.getenv("ADMIN_IDS", "")),
    database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./virex.db"),
    card_number=os.getenv("CARD_NUMBER", ""),
    card_owner=os.getenv("CARD_OWNER", ""),
    support_contact=os.getenv("SUPPORT_CONTACT", "@Parham88e"),
    marzban_enabled=os.getenv("MARZBAN_ENABLED", "false").lower() == "true",
    marzban_url=os.getenv("MARZBAN_URL", ""),
    marzban_username=os.getenv("MARZBAN_USERNAME", ""),
    marzban_password=os.getenv("MARZBAN_PASSWORD", ""),
)
