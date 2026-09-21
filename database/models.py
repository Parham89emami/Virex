from __future__ import annotations
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    wallet_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    orders: Mapped[list["Order"]] = relationship(back_populates="user")
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    volume_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    configs: Mapped[list["VPNConfig"]] = relationship(back_populates="product", cascade="all, delete-orphan")
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_uid: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    config_id: Mapped[int | None] = mapped_column(ForeignKey("vpn_configs.id"))
    plan_name: Mapped[str] = mapped_column(String(255), nullable=False)
    traffic_gb: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    price_toman: Mapped[int] = mapped_column(Integer, nullable=False)
    original_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    payment_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    receipt_file_id: Mapped[str | None] = mapped_column(String(255))
    receipt_file_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    user: Mapped[User] = relationship(back_populates="orders")
class VPNConfig(Base):
    __tablename__ = "vpn_configs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    config_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="available", index=True, nullable=False)
    sold_to_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sold_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    product: Mapped[Product] = relationship(back_populates="configs")
class Coupon(Base):
    __tablename__ = "coupons"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    discount_percent: Mapped[int | None] = mapped_column(Integer)
    discount_amount: Mapped[int | None] = mapped_column(Integer)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    usage_limit: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
class CouponUsage(Base):
    __tablename__ = "coupon_usages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coupon_id: Mapped[int] = mapped_column(ForeignKey("coupons.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    __table_args__ = (UniqueConstraint("coupon_id", "user_id"),)
class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
