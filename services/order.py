from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Coupon, CouponUsage, Order, Product, User, VPNConfig, WalletTransaction


async def get_or_create_user(session: AsyncSession, telegram_user: Any) -> User:
    user = (await session.execute(select(User).where(User.telegram_id == telegram_user.id))).scalar_one_or_none()
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


async def active_products(session: AsyncSession) -> list[Product]:
    return list((await session.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.volume_gb))).scalars().all())


async def coupon_price(session: AsyncSession, code: str, user_id: int, price: int):
    coupon = (await session.execute(select(Coupon).where(Coupon.code == code.strip().upper(), Coupon.is_active.is_(True)))).scalar_one_or_none()
    if not coupon:
        return price, None, "کد تخفیف معتبر نیست."
    if coupon.usage_limit is not None and coupon.used_count >= coupon.usage_limit:
        return price, None, "ظرفیت کد تخفیف تمام شده است."
    used = (await session.execute(select(CouponUsage.id).where(CouponUsage.coupon_id == coupon.id, CouponUsage.user_id == user_id))).scalar_one_or_none()
    if used:
        return price, None, "این کد قبلاً استفاده شده است."
    discount = coupon.discount_amount or price * (coupon.discount_percent or 0) // 100
    return max(0, price - discount), coupon, None


async def create_order(session: AsyncSession, user: User, product: Product, price: int, coupon: Coupon | None = None, payment_method: str = "card") -> Order:
    order = Order(order_uid=f"VIR-{uuid.uuid4().hex[:8].upper()}", user_id=user.id, product_id=product.id, plan_name=product.name, traffic_gb=product.volume_gb, duration_days=product.duration_days, price_toman=price, original_price=product.price, payment_method=payment_method)
    session.add(order)
    if coupon:
        coupon.used_count += 1
        session.add(CouponUsage(coupon_id=coupon.id, user_id=user.id))
    await session.flush()
    return order


async def pending_order(session: AsyncSession, telegram_id: int) -> Order | None:
    return (await session.execute(select(Order).join(Order.user).where(User.telegram_id == telegram_id, Order.payment_status == "pending").order_by(Order.created_at.desc()).limit(1))).scalar_one_or_none()


async def user_orders(session: AsyncSession, telegram_id: int) -> list[Order]:
    return list((await session.execute(select(Order).join(Order.user).where(User.telegram_id == telegram_id).order_by(Order.created_at.desc()))).scalars().all())


async def review_order(session: AsyncSession, order: Order, file_id: str, file_name: str) -> None:
    order.status = order.payment_status = "pending_review"
    order.receipt_file_id = file_id
    order.receipt_file_name = file_name
    await session.commit()


async def debit_wallet(session: AsyncSession, user: User, amount: int, description: str) -> bool:
    if amount < 0 or user.wallet_balance < amount:
        return False
    user.wallet_balance -= amount
    session.add(WalletTransaction(user_id=user.id, amount=-amount, transaction_type="debit", description=description))
    return True


async def approve_and_deliver(session: AsyncSession, order_id: int) -> tuple[Order | None, VPNConfig | None]:
    order = await session.get(Order, order_id)
    if not order or order.payment_status != "pending_review":
        return order, None
    config = (await session.execute(select(VPNConfig).where(VPNConfig.product_id == order.product_id, VPNConfig.status == "available").order_by(VPNConfig.id).limit(1))).scalar_one_or_none()
    if not config:
        return order, None
    result = await session.execute(
        update(VPNConfig)
        .where(VPNConfig.id == config.id, VPNConfig.status == "available")
        .values(status="sold", sold_to_user_id=order.user_id, order_id=order.id, sold_at=datetime.now(timezone.utc))
    )
    if result.rowcount != 1:
        await session.rollback()
        return order, None
    order.config_id = config.id
    order.status = "completed"
    order.payment_status = "approved"
    order.completed_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(order)
    return order, config
