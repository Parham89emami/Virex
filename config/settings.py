from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()
def parse_admin_ids(value: str) -> list[int]: return [int(x.strip()) for x in value.split(",") if x.strip().isdigit()]
@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: list[int]
    database_url: str
    card_number: str
    card_owner: str
    support_contact: str
raw_db = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./virex.db")
if raw_db.startswith("postgres://"): raw_db = raw_db.replace("postgres://", "postgresql+asyncpg://", 1)
elif raw_db.startswith("postgresql://") and "+asyncpg" not in raw_db: raw_db = raw_db.replace("postgresql://", "postgresql+asyncpg://", 1)
settings = Settings(os.getenv("BOT_TOKEN", ""), parse_admin_ids(os.getenv("ADMIN_IDS", "")), raw_db, os.getenv("CARD_NUMBER", ""), os.getenv("CARD_OWNER", ""), os.getenv("SUPPORT_CONTACT", "@VirexSupport"))
