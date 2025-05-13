"""
Seed data for live demo
──────────────────────
* 创建用户：Amy / Bob（新人）
* 各自发放指定优惠券
* 创建 3 家商户 + 4 个团购套餐
"""

import asyncio
import bcrypt
from datetime import datetime

from backend.database import async_session  # async_sessionmaker 实例
from backend.models import (
    User,
    Shop,
    Package,
    Coupon,
    UserCoupon,
    DiscountType,
    ExpiryType,
    CouponStatus,
)

# ────────────────────────── 基础数据 ────────────────────────── #

USERS = [
    dict(username="Amy", password_plain="Amy123!"),
    dict(username="Bob", password_plain="Bob123!"),
]

SHOPS = [
    dict(
        name="新发现（五角场万达店）",
        category="中餐",
        packages=[
            ("家庭小聚三人餐", 199),
            ("招牌甄选三人餐", 209),
        ],
    ),
    dict(
        name="茶百道（五角场中心店）",
        category="奶茶",
        packages=[
            ("葡萄系列3选1", 11),
        ],
    ),
    dict(
        name="喜茶（五角场万达店）",
        category="奶茶",
        packages=[
            ("时令白芭乐2选1", 19),
        ],
    ),
]

COUPONS_AMY = [
    dict(  # 0.1 元秒杀券：减到 0.1 元，最高抵 20 元
        name="0.1元秒杀券",
        discount_type=DiscountType.fixed_amount,
        discount_value=0.1,
        max_discount=20,
        description="无门槛，全品类适用",
    ),
    dict(  # 5 折奖励券
        name="5折奖励券",
        discount_type=DiscountType.discount,
        discount_value=0.5,  # 支付 50%
        description="无门槛，全品类适用",
    ),
    dict(  # 西餐减 150 元券
        name="西餐减150元券",
        discount_type=DiscountType.deduction,
        discount_value=150,
        description="无门槛，仅限西餐品类",
        category="西餐",
    ),
]

COUPONS_BOB = [
    dict(  # 喜茶免单券，最高抵 20 元
        name="喜茶免单券",
        discount_type=DiscountType.fixed_amount,
        discount_value=0.0,
        max_discount=20,
        description="限喜茶（五角场万达店）使用",
        shop_restriction="喜茶（五角场万达店）",
    ),
    dict(  # 6 折奖励券
        name="6折奖励券",
        discount_type=DiscountType.discount,
        discount_value=0.6,  # 支付 60%
        description="无门槛，全品类适用",
    ),
]

# ────────────────────────── 种子逻辑 ────────────────────────── #


async def seed():
    async with async_session() as db:
        # 1. 创建用户
        user_id_map: dict[str, int] = {}
        for u in USERS:
            hashed = (
                bcrypt.hashpw(u["password_plain"].encode("utf-8"), bcrypt.gensalt())
                .decode("utf-8")
            )
            user = User(username=u["username"], password_hash=hashed)
            db.add(user)
            await db.flush()
            user_id_map[u["username"]] = user.id

        # 2. 创建优惠券
        async def create_coupons(specs, owner_username):
            for spec in specs:
                coupon = Coupon(
                    **spec,
                    min_spend=0,
                    expiry_type=ExpiryType.unlimited,
                )
                db.add(coupon)
                await db.flush()  # 获得 coupon.id

                # 用户券关系
                uc = UserCoupon(
                    user_id=user_id_map[owner_username],
                    coupon_id=coupon.id,
                    status=CouponStatus.unused,
                    claimed_at=datetime.utcnow(),
                    expires_at=None,
                )
                db.add(uc)

        await create_coupons(COUPONS_AMY, "Amy")
        await create_coupons(COUPONS_BOB, "Bob")

        # 3. 创建商户 & 套餐
        for s in SHOPS:
            shop = Shop(name=s["name"], category=s["category"])
            db.add(shop)
            await db.flush()
            for title, price in s["packages"]:
                pkg = Package(
                    title=title,
                    price=price,
                    description=f"{title}（演示套餐）",
                    contents="请根据需要自行修改",
                    sales=0,
                    shop_id=shop.id,
                )
                db.add(pkg)

        await db.commit()
        print("✅ 数据准备完毕！")


if __name__ == "__main__":
    asyncio.run(seed())
