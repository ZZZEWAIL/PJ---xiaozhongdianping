"""
Script to reset and seed the database for demonstration purposes.
- Drops all tables (with user confirmation)
- Recreates tables
- Inserts demo data for users, shops, packages, coupons, and user_coupons

Usage: python generate_demo_data.py
"""
import sys
import getpass
from backend.database import sync_engine, create_database
from backend.models import Base, DiscountType, ExpiryType, CouponStatus, User, Shop, Package, Coupon, UserCoupon
from sqlalchemy.orm import Session
import bcrypt
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Demo data (copied/adapted from backend/seed_demo_data.py)
USERS = [
    dict(username="Amy", password_plain="Amy123!"),
    dict(username="Bob", password_plain="Bob123!"),
]

SHOPS = [
    dict(
        name="新发现（五角场万达店）",
        category="中餐",
        rating=4.7,
        price_range="¥¥",
        avg_cost=120.0,
        name_pinyin="xinfaxian(wujiaochang wanda dian)",
        category_pinyin="zhongcan",
        address="上海市杨浦区邯郸路600号万达广场3层301室",
        phone="021-55555555",
        business_hours="10:00-22:00",
        image_url="https://example.com/images/xinfaxian.jpg",
        packages=[
            dict(
                title="家庭小聚三人餐",
                price=199,
                description="适合3人分享的美味套餐，包含多种经典菜品",
                contents="红烧肉×1 + 宫保鸡丁×1 + 干锅土豆片×1 + 蒜蓉油麦菜×1 + 米饭×3 + 饮料×3",
                sales=128
            ),
            dict(
                title="招牌甄选三人餐",
                price=209,
                description="厨师推荐的3人精选套餐，包含店内招牌菜品",
                contents="招牌烤鸭×1 + 鱼香肉丝×1 + 水煮牛肉×1 + 上汤娃娃菜×1 + 米饭×3 + 甜点×3",
                sales=156
            ),
        ],
    ),
    dict(
        name="茶百道（五角场中心店）",
        category="奶茶",
        rating=4.5,
        price_range="¥",
        avg_cost=18.0,
        name_pinyin="chabaidao(wujiaochang zhongxin dian)",
        category_pinyin="naicha",
        address="上海市杨浦区淞沪路77号大西洋百货1层",
        phone="021-66666666",
        business_hours="09:00-22:30",
        image_url="https://example.com/images/chabaidao.jpg",
        packages=[
            dict(
                title="葡萄系列3选1",
                price=11,
                description="招牌葡萄系列饮品优惠券，可3选1",
                contents="水晶葡萄×1 或 葡萄啵啵×1 或 葡萄冻冻×1（大杯）",
                sales=532
            ),
        ],
    ),
    dict(
        name="喜茶（五角场万达店）",
        category="奶茶",
        rating=4.8,
        price_range="¥¥",
        avg_cost=30.0,
        name_pinyin="xicha(wujiaochang wanda dian)",
        category_pinyin="naicha",
        address="上海市杨浦区邯郸路600号万达广场2层201室",
        phone="021-77777777",
        business_hours="10:00-22:00",
        image_url="https://example.com/images/xicha.jpg",
        packages=[
            dict(
                title="时令白芭乐2选1",
                price=19,
                description="精选白芭乐水果制作，口感清爽",
                contents="满杯白芭乐×1 或 芝芝莓莓×1（标准杯）",
                sales=423
            ),
            dict(
                title="多肉车厘双人分享装",
                price=36,
                description="人气多肉系列，2杯组合特惠",
                contents="多肉葡萄×1 + 多肉车厘×1（标准杯）",
                sales=265
            ),
        ],
    ),
    dict(
        name="汉堡王（五角场合生汇店）",
        category="西餐",
        rating=4.4,
        price_range="¥¥",
        avg_cost=45.0,
        name_pinyin="hanbaowang(wujiaochang hesheng hui dian)",
        category_pinyin="xican",
        address="上海市杨浦区淞沪路1号合生汇商场B1层",
        phone="021-88888888",
        business_hours="09:00-21:30",
        image_url="https://example.com/images/burgerking.jpg",
        packages=[
            dict(
                title="双人超值套餐",
                price=75,
                description="经典汉堡双人套餐，超值享受",
                contents="皇堡×1 + 辣味皇堡×1 + 薯条（中）×2 + 可乐（中）×2",
                sales=312
            ),
            dict(
                title="家庭欢享四人餐",
                price=159,
                description="全家欢聚首选，多种美食一次满足",
                contents="皇堡×2 + 辣味皇堡×1 + 芝士汉堡×1 + 薯条（大）×2 + 洋葱圈×1 + 可乐（中）×4",
                sales=178
            ),
        ],
    ),
]

COUPONS_AMY = [
    dict(
        name="0.1元秒杀券",
        discount_type=DiscountType.fixed_amount,
        discount_value=0.1,
        max_discount=20,
        description="无门槛，全品类适用",
    ),
    dict(
        name="5折奖励券",
        discount_type=DiscountType.discount,
        discount_value=0.5,
        description="无门槛，全品类适用",
    ),
    dict(
        name="西餐减150元券",
        discount_type=DiscountType.deduction,
        discount_value=150,
        description="无门槛，仅限西餐品类",
        category="西餐",
    ),
]

COUPONS_BOB = [
    dict(
        name="喜茶免单券",
        discount_type=DiscountType.fixed_amount,
        discount_value=0.0,
        max_discount=20,
        description="限喜茶（五角场万达店）使用",
        shop_restriction="喜茶（五角场万达店）",
    ),
    dict(
        name="6折奖励券",
        discount_type=DiscountType.discount,
        discount_value=0.6,
        description="无门槛，全品类适用",
    ),
]

def prompt_confirm() -> bool:
    """Prompt the user for confirmation before destructive actions."""
    print("WARNING: This will DROP ALL TABLES and DELETE ALL DATA in the database!")
    ans = input("Type 'yes' to continue, or anything else to abort: ").strip().lower()
    return ans == 'yes'

def drop_all_tables():
    """Drop all tables in the database."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=sync_engine)
    print("All tables dropped.")

def create_all_tables():
    """Create all tables in the database."""
    print("Creating all tables...")
    Base.metadata.create_all(bind=sync_engine)
    print("All tables created.")

def insert_demo_data():
    """Insert demo data for users, shops, packages, coupons, and user_coupons."""
    print("Inserting demo data...")
    with Session(sync_engine) as db:
        user_id_map: Dict[str, int] = {}
        # Users
        for u in USERS:
            hashed = bcrypt.hashpw(u["password_plain"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            user = User(username=u["username"], password_hash=hashed)
            db.add(user)
            db.flush()
            user_id_map[u["username"]] = user.id
        # Coupons
        def create_coupons(specs, owner_username):
            for spec in specs:
                coupon = Coupon(
                    **spec,
                    min_spend=0,
                    expiry_type=ExpiryType.unlimited,
                )
                db.add(coupon)
                db.flush()
                uc = UserCoupon(
                    user_id=user_id_map[owner_username],
                    coupon_id=coupon.id,
                    status=CouponStatus.unused,
                    claimed_at=datetime.utcnow(),
                    expires_at=None,
                )
                db.add(uc)
        create_coupons(COUPONS_AMY, "Amy")
        create_coupons(COUPONS_BOB, "Bob")
        # Shops & Packages
        for s in SHOPS:
            shop = Shop(
                name=s["name"],
                category=s["category"],
                rating=s["rating"],
                price_range=s["price_range"],
                avg_cost=s["avg_cost"],
                name_pinyin=s["name_pinyin"],
                category_pinyin=s["category_pinyin"],
                address=s["address"],
                phone=s["phone"],
                business_hours=s["business_hours"],
                image_url=s["image_url"],
            )
            db.add(shop)
            db.flush()
            for pkg in s["packages"]:
                package = Package(
                    title=pkg["title"],
                    price=pkg["price"],
                    description=pkg["description"],
                    contents=pkg["contents"],
                    sales=pkg["sales"],
                    shop_id=shop.id,
                )
                db.add(package)
        db.commit()
    print("Demo data inserted.")

def main():
    """Main entry point for the script."""
    create_database()
    if not prompt_confirm():
        print("Aborted by user.")
        sys.exit(0)
    drop_all_tables()
    create_all_tables()
    insert_demo_data()
    print("All done!")

if __name__ == "__main__":
    main()
