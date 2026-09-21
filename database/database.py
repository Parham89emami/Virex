from __future__ import annotations
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config.settings import settings
from database.models import Base, Product

engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        from sqlalchemy import select
        if not (await session.execute(select(Product).limit(1))).scalar_one_or_none():
            session.add_all([
                Product(name="VPN کینگ ۵ گیگ", volume_gb=5, duration_days=30, price=30000),
                Product(name="VPN کینگ ۱۰ گیگ", volume_gb=10, duration_days=30, price=60000),
                Product(name="VPN کینگ ۲۰ گیگ", volume_gb=20, duration_days=30, price=120000),
                Product(name="VPN کینگ ۵۰ گیگ", volume_gb=50, duration_days=30, price=200000),
                Product(name="VPN کینگ ۱۰۰ گیگ", volume_gb=100, duration_days=30, price=345000),
            ])
            await session.commit()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
