from __future__ import annotations
from collections.abc import AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config.settings import settings
from database.models import Base, Product
engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
DEFAULT_PRODUCTS = (("Virex 5GB",5,30,30000),("Virex 10GB",10,30,60000),("Virex 20GB",20,30,120000),("Virex 50GB",50,30,200000),("Virex 100GB",100,30,345000))
async def init_db() -> None:
    async with engine.begin() as connection: await connection.run_sync(Base.metadata.create_all)
    async with async_session_factory() as session:
        if (await session.execute(select(Product.id).limit(1))).scalar_one_or_none() is None:
            session.add_all([Product(name=n, volume_gb=v, duration_days=d, price=p) for n,v,d,p in DEFAULT_PRODUCTS]); await session.commit()
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session: yield session
