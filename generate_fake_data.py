from sqlalchemy.orm import Session
from backend.models import Shop, ShopImage
from backend.database import SessionLocal
from pypinyin import pinyin, Style
from faker import Faker
from sqlalchemy.sql import text
import random

fake = Faker('zh_CN')

categories = ["火锅", "奶茶", "海鲜", "烧烤", "川菜", "粤菜", "甜品", "快餐", "日料", "韩料"]

# 示例图片 URL 列表
sample_images = [
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1552566626-52f8b828add9?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1512058564366-2b4e5a4f5f5c?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1504672281656-e4981d70414b?q=80&w=800&auto=format&fit=crop"
]

def generate_unique_shop_name(existing_names, suffix_options):
    max_attempts = 100
    for _ in range(max_attempts):
        prefix = fake.company_prefix()
        suffix = random.choice(suffix_options)
        shop_name = f"{prefix}{suffix}"
        if shop_name not in existing_names:
            existing_names.add(shop_name)
            return shop_name
    raise ValueError("Unable to generate a unique shop name after maximum attempts")

def generate_fake_shops_and_images():
    db: Session = SessionLocal()
    try:
        # 禁用外键约束
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        # 清空表并验证
        db.execute(text("TRUNCATE TABLE shop_images;"))
        db.execute(text("TRUNCATE TABLE shops;"))
        db.execute(text("TRUNCATE TABLE search_history;"))
        
        # 验证是否清空成功
        shop_count = db.execute(text("SELECT COUNT(*) FROM shops;")).scalar()
        if shop_count != 0:
            raise RuntimeError("Failed to truncate shops table: table not empty")
        
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()

        existing_names = set()
        suffix_options = ["店", "馆", "屋", "大师", "之家"]

        for i in range(50):
            shop_name = generate_unique_shop_name(existing_names, suffix_options)
            pinyin_list = pinyin(shop_name, style=Style.NORMAL)
            name_pinyin = ' '.join([item[0] for item in pinyin_list])

            category = random.choice(categories)
            category_pinyin_list = pinyin(category, style=Style.NORMAL)
            category_pinyin = ' '.join([item[0] for item in category_pinyin_list])

            rating = round(random.uniform(3.0, 5.0), 1)
            avg_cost = round(random.uniform(10, 150), 2)
            price_range = f"¥{int(avg_cost * 0.8)}-{int(avg_cost * 1.2)}"
            address = fake.address()
            phone = fake.phone_number()
            business_hours = f"{random.randint(8, 11)}:00-{random.randint(20, 23)}:00"

            shop = Shop(
                name=shop_name,
                category=category,
                rating=rating,
                price_range=price_range,
                avg_cost=avg_cost,
                name_pinyin=name_pinyin,
                category_pinyin=category_pinyin,
                address=address,
                phone=phone,
                business_hours=business_hours,
                image_url=None
            )
            db.add(shop)
            db.flush()

            # 为每个商家生成至少三张图片（允许重复）
            num_images = random.randint(3, 5)  # 随机生成3到5张图片
            for j in range(num_images):
                shop_image = ShopImage(
                    shop_id=shop.id,
                    image_url=random.choice(sample_images)  # 允许重复选择图片
                )
                db.add(shop_image)

            print(f"Added shop: {shop.name} with pinyin: {shop.name_pinyin}, category: {shop.category}, category_pinyin: {shop.category_pinyin}, {num_images} images")

        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_fake_shops_and_images()