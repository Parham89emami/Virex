from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Coupon, CouponUsage, Order, Product, User, VPNConfig, WalletTransaction

logger = logging.getLogger(__name__)

async def get_or_create_user(session: AsyncSession, telegram_user: Any) -> User:
    user = (await session.execute(select(User).where(User.telegram_id == telegram_user.id))).scalar_one_or_none()
    if user:
        user.username, user.first_name, user.last_name = telegram_user.username, telegram_user.first_name, telegram_user.last_name
        await session.commit()
        return user
    user = User(telegram_id=telegram_user.id, username=telegram_user.username, first_name=telegram_user.first_name, last_name=telegram_user.last_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def active_products(session: AsyncSession) -> list[Product]:
    return list((await session.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.volume_gb))).scalars().all())

async def calculate_coupon(session: AsyncSession, code: str, user_id: int, price: int) -> tuple[int, Coupon | None, str | None]:
    coupon = (await session.execute(select(Coupon).where(Coupon.code == code.strip().upper(), Coupon.is_active.is_(True)))).scalar_one_or_none()
    if not coupon: return price, None, "کد تخفیف معتبر یا فعال نیست."
    now = datetime.now(timezone.utc)
    if coupon.expires_at and coupon.expires_at.replace(tzinfo=timezone.utc) < now: return price, None, "تاریخ کد تخفیف گذشته است."
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit: return price, None, "ظرفیت کد تخفیف تمام شده است."
    if (await session.execute(select(CouponUsage.id).where(CouponUsage.coupon_id == coupon.id, CouponUsage.user_id == user_id))).scalar_one_or_none(): return price, None, "این کد را قبلاً استفاده کرده‌اید."
    discount = coupon.discount_amount or price * (coupon.discount_percent or 0) // 100
    return max(0, price - discount), coupon, None

async def create_order_for_user(session: AsyncSession, user: User, product: Product, price: int | None = None, coupon: Coupon | None = None) -> Order:
    amount = product.price if price is None else price
    order = Order(order_uid=f"VIR-{uuid.uuid4().hex[:8].upper()}", user_id=user.id, product_id=product.id, plan_name=product.name, traffic_gb=product.volume_gb, duration_days=product.duration_days, price_toman=amount, original_price=product.price)
    session.add(order)
    if coupon:
        coupon.used_count += 1
        session.add(CouponUsage(coupon_id=coupon.id, user_id=user.id))
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise
    await session.refresh(order)
    return order

async def get_latest_pending_order_for_user(session: AsyncSession, telegram_id: int) -> Order | None:
    return (await session.execute(select(Order).join(Order.user).where(User.telegram_id == telegram_id, Order.payment_status == "pending").order_by(Order.created_at.desc()).limit(1))).scalar_one_or_none()

async def get_all_orders_for_user(session: AsyncSession, telegram_id: int) -> list[Order]:
    return list((await session.execute(select(Order).join(Order.user).where(User.telegram_id == telegram_id).order_by(Order.created_at.desc()))).scalars().all())

async def update_order_review(session: AsyncSession, order: Order, file_id: str, file_name: str) -> None:
    order.payment_status, order.status = "pending_review", "pending_review"
    order.receipt_file_id, order.receipt_file_name = file_id, file_name
    await session.commit()

async def approve_and_deliver(session: AsyncSession, order_id: int) -> tuple[Order | None, VPNConfig | None]:
    order = (await session.execute(select(Order).where(Order.id == order_id))).scalar_one_or_none()
    if not order or order.payment_status != "pending_review": return order, None
    config = (await session.execute(select(VPNConfig).where(VPNConfig.product_id == order.product_id, VPNConfig.status == "available").order_by(VPNConfig.id).limit(1))).scalar_one_or_none()
    if not config: return order, None
    claimed = await session.execute(update(VPNConfig).where(VPNConfig.id == config.id, VPNConfig.status == "available").values(status="sold", sold_to_user_id=order.user_id, order_id=order.id, sold_at=datetime.now(timezone.utc)))
    if claimed.rowcount != 1:
        await session.rollback(); return order, None
    order.config_id, order.status, order.payment_status, order.completed_at = config.id, "completed", "approved", datetime.now(timezone.utc)
    await session.commit(); await session.refresh(order)
    return order, config

async def charge_wallet(session: AsyncSession, user: User, amount: int, description: str) -> bool:
    if amount < 0 or user.wallet_balance < amount: return False
    user.wallet_balance -= amount
    session.add(WalletTransaction(user_id=user.id, amount=-amount, transaction_type="debit", description=description))
    await session.commit()
    return True
