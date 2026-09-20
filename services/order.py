from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models import Order, Payment, User
from services.vpn import VPNPlan


async def get_active_order_for_user(session: AsyncSession, user_id: int) -> Order | None:
    result = await session.execute(
        select(Order).where(
            Order.user_id == user_id,
            Order.status.in_(["pending", "pending_review"]),
        ).order_by(Order.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_or_create_user(session: AsyncSession, telegram_user: Any) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_user.id)
        session.add(user)
    user.username = telegram_user.username
    user.first_name = telegram_user.first_name
    user.last_name = telegram_user.last_name
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
    order.payment = Payment(order=order, amount=plan.price_toman, status="pending")
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_latest_pending_order_for_user(session: AsyncSession, telegram_id: int) -> Order | None:
    result = await session.execute(
        select(Order).join(Order.user).where(
            User.telegram_id == telegram_id,
            Order.status == "pending",
            Order.payment_status == "pending",
        ).order_by(Order.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_all_orders_for_user(session: AsyncSession, telegram_id: int) -> list[Order]:
    result = await session.execute(
        select(Order).join(Order.user).where(User.telegram_id == telegram_id)
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().all())


async def update_order_review(
    session: AsyncSession,
    order: Order,
    file_id: str,
    file_name: str,
    receipt_type: str,
) -> None:
    if order.payment_status != "pending":
        return
    order.payment_status = "pending_review"
    order.status = "pending_review"
    order.receipt_file_id = file_id
    order.receipt_file_name = file_name
    if order.payment is None:
        order.payment = Payment(order=order, amount=order.price_toman)
    order.payment.status = "pending_review"
    order.payment.receipt_file_id = file_id
    order.payment.receipt_type = receipt_type
    await session.commit()


async def get_pending_orders(session: AsyncSession) -> list[Order]:
    result = await session.execute(
        select(Order).options(selectinload(Order.user), selectinload(Order.payment))
        .where(Order.payment_status == "pending_review")
        .order_by(Order.created_at.asc())
    )
    return list(result.scalars().all())


async def get_order_by_id(session: AsyncSession, order_id: int) -> Order | None:
    result = await session.execute(
        select(Order).options(selectinload(Order.user), selectinload(Order.payment))
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def update_order_status(
    session: AsyncSession,
    order_id: int,
    approved: bool,
    reviewed_by: int,
    rejection_reason: str | None = None,
) -> Order | None:
    order = await get_order_by_id(session, order_id)
    if order is None or order.payment_status != "pending_review":
        return None
    order.status = "approved" if approved else "rejected"
    order.payment_status = "paid" if approved else "rejected"
    if order.payment is None:
        order.payment = Payment(order=order, amount=order.price_toman)
    order.payment.status = "paid" if approved else "rejected"
    order.payment.rejection_reason = None if approved else rejection_reason
    order.payment.reviewed_at = datetime.now(timezone.utc)
    order.payment.reviewed_by = reviewed_by
    await session.commit()
    await session.refresh(order)
    return order
