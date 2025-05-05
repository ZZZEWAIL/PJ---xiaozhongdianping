"""
订单观察者模块（观察者模式）
定义订单创建后的观察者响应逻辑，实现事件触发后的模块解耦处理。
"""
from abc import ABC, abstractmethod
from backend.models import Order, Package, UserCoupon, CouponStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

class OrderObserver(ABC):
    """
    抽象观察者基类，所有订单事件观察者需继承并实现该接口。
    """
    @abstractmethod
    async def on_order_created(self, order: Order, db: AsyncSession):
        """
        处理订单创建事件。
        """
        pass

class PackageSalesObserver(OrderObserver):
    """
    观察者：订单创建时更新套餐销量。
    """
    async def on_order_created(self, order: Order, db: AsyncSession):
        # 获取订单对应的套餐
        package = await db.get(Package, order.package_id)
        if package:
            # 销量 +1
            package.sales += 1
            await db.commit()

class CouponUsageObserver(OrderObserver):
    """
    观察者：订单使用优惠券后，将该用户券状态设置为已使用。
    """
    async def on_order_created(self, order: Order, db: AsyncSession):
        if order.coupon_id:
            # 查询该用户尚未使用的对应优惠券
            result = await db.execute(select(UserCoupon).where(
                UserCoupon.user_id == order.user_id,
                UserCoupon.coupon_id == order.coupon_id,
                UserCoupon.status == CouponStatus.unused
            ).limit(1))
            user_coupon = result.scalars().first()
            if user_coupon:
                user_coupon.status = CouponStatus.used
                await db.commit()

# 注册的观察者列表
_observers: List[OrderObserver] = []

def register_observer(observer: OrderObserver):
    """
    注册一个订单事件观察者。
    """
    _observers.append(observer)

async def notify_order_created(order: Order, db: AsyncSession):
    """
    通知所有已注册的观察者：订单已创建。
    """
    for obs in _observers:
        try:
            await obs.on_order_created(order, db)
        except Exception as e:
            # 某个观察者失败时打印日志，不影响其他观察者执行
            print(f"观察者 {obs.__class__.__name__} 执行失败: {e}")
