from __future__ import annotations
import uuid
from datetime import datetime,timezone
from typing import Any
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Coupon,CouponUsage,Order,Product,User,VPNConfig,WalletTransaction
async def get_or_create_user(s:AsyncSession,t:Any)->User:
 u=(await s.execute(select(User).where(User.telegram_id==t.id))).scalar_one_or_none()
 if u: u.username,u.first_name,u.last_name=t.username,t.first_name,t.last_name; await s.commit(); return u
 u=User(telegram_id=t.id,username=t.username,first_name=t.first_name,last_name=t.last_name); s.add(u); await s.commit(); await s.refresh(u); return u
async def active_products(s): return list((await s.execute(select(Product).where(Product.is_active.is_(True)).order_by(Product.volume_gb))).scalars().all())
async def coupon_price(s,code,user_id,price):
 c=(await s.execute(select(Coupon).where(Coupon.code==code.strip().upper(),Coupon.is_active.is_(True)))).scalar_one_or_none()
 if not c:return price,None,'کد تخفیف معتبر نیست.'
 if c.usage_limit is not None and c.used_count>=c.usage_limit:return price,None,'ظرفیت کد تخفیف تمام شده است.'
 if (await s.execute(select(CouponUsage.id).where(CouponUsage.coupon_id==c.id,CouponUsage.user_id==user_id))).scalar_one_or_none():return price,None,'این کد قبلاً استفاده شده است.'
 return max(0,price-(c.discount_amount or price*(c.discount_percent or 0)//100)),c,None
async def create_order(s,user,product,price=None,coupon=None):
 o=Order(order_uid=f'VIR-{uuid.uuid4().hex[:8].upper()}',user_id=user.id,product_id=product.id,plan_name=product.name,traffic_gb=product.volume_gb,duration_days=product.duration_days,price_toman=product.price if price is None else price,original_price=product.price); s.add(o)
 if coupon: coupon.used_count+=1; s.add(CouponUsage(coupon_id=coupon.id,user_id=user.id))
 await s.commit(); await s.refresh(o); return o
async def pending_order(s,tid): return (await s.execute(select(Order).join(Order.user).where(User.telegram_id==tid,Order.payment_status=='pending').order_by(Order.created_at.desc()).limit(1))).scalar_one_or_none()
async def user_orders(s,tid): return list((await s.execute(select(Order).join(Order.user).where(User.telegram_id==tid).order_by(Order.created_at.desc()))).scalars().all())
async def review_order(s,o,file_id,file_name): o.status=o.payment_status='pending_review';o.receipt_file_id=file_id;o.receipt_file_name=file_name;await s.commit()
async def debit_wallet(s,u,amount,description):
 if amount<0 or u.wallet_balance<amount:return False
 u.wallet_balance-=amount;s.add(WalletTransaction(user_id=u.id,amount=-amount,transaction_type='debit',description=description));await s.commit();return True
async def approve_and_deliver(s,order_id):
 o=(await s.execute(select(Order).where(Order.id==order_id))).scalar_one_or_none()
 if not o or o.payment_status!='pending_review':return o,None
 c=(await s.execute(select(VPNConfig).where(VPNConfig.product_id==o.product_id,VPNConfig.status=='available').order_by(VPNConfig.id).limit(1))).scalar_one_or_none()
 if not c:return o,None
 r=await s.execute(update(VPNConfig).where(VPNConfig.id==c.id,VPNConfig.status=='available').values(status='sold',sold_to_user_id=o.user_id,order_id=o.id,sold_at=datetime.now(timezone.utc)))
 if r.rowcount!=1:await s.rollback();return o,None
 o.config_id=c.id;o.status='completed';o.payment_status='approved';o.completed_at=datetime.now(timezone.utc);await s.commit();await s.refresh(o);return o,c
