from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from database.models import Base, Product

logger = logging.getLogger(__name__)
engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
_instance_lock_connection: AsyncConnection | None = None

DEFAULT_PRODUCTS = {
    5: ("Virex 5GB", 30, 30_000),
    10: ("Virex 10GB", 30, 60_000),
    20: ("Virex 20GB", 30, 120_000),
    50: ("Virex 50GB", 30, 200_000),
    100: ("Virex 100GB", 30, 345_000),
}


async def acquire_instance_lock() -> None:
    """Allow only one Railway polling process for a PostgreSQL database."""
    global _instance_lock_connection
    if not settings.database_url.startswith("postgresql+"):
        logger.warning("Polling instance lock is only enforced with PostgreSQL")
        return
    connection = await engine.connect()
    locked = (await connection.execute(text("SELECT pg_try_advisory_lock(:lock_key)"), {"lock_key": settings.instance_lock_key})).scalar()
    if not locked:
        await connection.close()
        raise RuntimeError("Another Virex polling instance is already running.")
    _instance_lock_connection = connection


async def release_instance_lock() -> None:
    global _instance_lock_connection
    if _instance_lock_connection is not None:
        await _instance_lock_connection.close()
        _instance_lock_connection = None


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        products = (await session.execute(select(Product))).scalars().all()
        by_volume = {product.volume_gb: product for product in products}
        for volume, (name, days, price) in DEFAULT_PRODUCTS.items():
            product = by_volume.get(volume)
            if product is None:
                session.add(Product(name=name, volume_gb=volume, duration_days=days, price=price))
            else:
                product.name, product.duration_days, product.price, product.is_active = name, days, price, True
        await session.commit()
    logger.info("Database initialized")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
