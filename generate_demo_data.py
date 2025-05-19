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
from typing import Dict

# Demo data (copied/adapted from backend/seed_demo_data.py)
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
            shop = Shop(name=s["name"], category=s["category"])
            db.add(shop)
            db.flush()
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
