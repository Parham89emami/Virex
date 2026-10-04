from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Order, User, WalletTransaction, WalletTopupRequest


async def get_or_create_user(session: AsyncSession, telegram_user: Any) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        await session.commit()
        return user
    user = User(telegram_id=telegram_user.id, username=telegram_user.username, first_name=telegram_user.first_name, last_name=telegram_user.last_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_order_for_user(session: AsyncSession, user: User, plan_name: str, traffic_gb: int, duration_days: int, price_toman: int) -> Order:
    order = Order(
        order_uid=f"VIR-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        plan_name=plan_name,
        traffic_gb=traffic_gb,
        duration_days=duration_days,
        price_toman=price_toman,
    )
    session.add(order)
    await session.commit()
    await session.refresh(order)
    return order


async def get_latest_pending_order_for_user(session: AsyncSession, telegram_id: int) -> Order | None:
    result = await session.execute(
        select(Order).join(Order.user).where(User.telegram_id == telegram_id, Order.payment_status == "pending").order_by(Order.created_at.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def get_all_orders_for_user(session: AsyncSession, telegram_id: int) -> list[Order]:
    result = await session.execute(select(Order).join(Order.user).where(User.telegram_id == telegram_id).order_by(Order.created_at.desc()))
    return list(result.scalars().all())


async def update_order_review(session: AsyncSession, order: Order, file_id: str, file_name: str) -> None:
    order.payment_status = "pending_review"
    order.receipt_file_id = file_id
    order.receipt_file_name = file_name
    await session.commit()


async def get_pending_orders(session: AsyncSession) -> list[Order]:
    result = await session.execute(select(Order).where(Order.payment_status == "pending_review").order_by(Order.created_at.asc()))
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


async def create_wallet_topup_request(session: AsyncSession, user: User, amount_toman: int) -> WalletTopupRequest:
    request = WalletTopupRequest(
        request_uid=f"TOPUP-{uuid.uuid4().hex[:8].upper()}",
        user_id=user.id,
        amount_toman=amount_toman,
        status="pending",
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return request


async def update_wallet_topup_receipt(session: AsyncSession, topup_request: WalletTopupRequest, file_id: str, file_name: str) -> None:
    topup_request.receipt_file_id = file_id
    topup_request.receipt_file_name = file_name
    await session.commit()


async def get_pending_topup_requests(session: AsyncSession) -> list[WalletTopupRequest]:
    result = await session.execute(select(WalletTopupRequest).where(WalletTopupRequest.status == "pending").order_by(WalletTopupRequest.created_at.asc()))
    return list(result.scalars().all())


async def get_topup_request_by_id(session: AsyncSession, topup_id: int) -> WalletTopupRequest | None:
    return await session.get(WalletTopupRequest, topup_id)


async def approve_wallet_topup(session: AsyncSession, topup_request: WalletTopupRequest, admin_id: int) -> bool:
    """Approve wallet topup with atomic transaction. Returns True if approved, False if already approved/rejected."""
    if topup_request.status != "pending":
        return False

    user = await session.get(User, topup_request.user_id)
    if not user:
        return False

    user.wallet_balance += topup_request.amount_toman

    transaction = WalletTransaction(
        user_id=user.id,
        amount_toman=topup_request.amount_toman,
        transaction_type="topup_success",
        reference_id=str(topup_request.id),
        description=f"شارژ کیف پول - درخواست {topup_request.request_uid}",
    )
    session.add(transaction)

    topup_request.status = "approved"
    topup_request.reviewed_by_admin = admin_id

    await session.commit()
    await session.refresh(topup_request)
    return True


async def reject_wallet_topup(session: AsyncSession, topup_request: WalletTopupRequest, admin_id: int) -> bool:
    """Reject wallet topup. Returns True if rejected, False if already approved/rejected."""
    if topup_request.status != "pending":
        return False

    topup_request.status = "rejected"
    topup_request.reviewed_by_admin = admin_id

    await session.commit()
    await session.refresh(topup_request)
    return True
