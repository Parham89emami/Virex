from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, User
from services.vpn import VPNPlan


async def get_active_order_for_user(session: AsyncSession, user_id: int) -> Order | None:
    result = await session.execute(
        select(Order)
        .where(
            Order.user_id == user_id,
            Order.payment_status.in_(["pending", "pending_review"]),
        )
        .order_by(Order.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_or_create_user(session: AsyncSession, telegram_user: Any) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        await session.commit()
        return user

    user = User(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
        last_name=telegram_user.last_name,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_order_for_user(session: AsyncSession, user: User, plan: VPNPlan) -> Order:
    existing = await get_active_order_for_user(session, user.id)
    if existing is not None:
        return existing

    order = Order(
        order_uid=f"VIR-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        plan_name=plan.name,
        traffic_gb=plan.traffic_gb,
        duration_days=plan.duration_days,
        price_toman=plan.price_toman,
        status="pending",
        payment_status="pending",
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_latest_pending_order_for_user(session: AsyncSession, telegram_id: int) -> Order | None:
    result = await session.execute(
        select(Order)
        .join(Order.user)
        .where(User.telegram_id == telegram_id, Order.payment_status.in_(["pending", "pending_review"]))
        .order_by(Order.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_all_orders_for_user(session: AsyncSession, telegram_id: int) -> list[Order]:
    result = await session.execute(
        select(Order)
        .join(Order.user)
        .where(User.telegram_id == telegram_id)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def update_order_review(session: AsyncSession, order: Order, file_id: str, file_name: str) -> None:
    order.payment_status = "pending_review"
    order.status = "pending"
    order.receipt_file_id = file_id
    order.receipt_file_name = file_name
    await session.commit()


async def get_pending_orders(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order)
        .where(Order.payment_status == "pending_review")
        .order_by(Order.created_at.asc())
    )
    return list(result.scalars().all())


async def update_order_status(session: AsyncSession, order_id: int, status: str, payment_status: str) -> Order | None:
    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if order is None:
        return None
    order.status = status
    order.payment_status = payment_status
    await session.commit()
    await session.refresh(order)
    return order
