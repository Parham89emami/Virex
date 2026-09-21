from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from database.models import Base, Product

logger = logging.getLogger(__name__)
engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

DEFAULT_PRODUCTS = {
    5: ("Virex 5GB", 30, 30_000),
    10: ("Virex 10GB", 30, 60_000),
    20: ("Virex 20GB", 30, 120_000),
    50: ("Virex 50GB", 30, 200_000),
    100: ("Virex 100GB", 30, 345_000),
}


async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text("DROP TABLE IF EXISTS coupon_usages"))
        await connection.execute(text("DROP TABLE IF EXISTS coupons"))
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
    logger.info("Database initialized without coupon tables")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
