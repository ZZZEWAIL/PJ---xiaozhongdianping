from sqlalchemy.orm import Session
from backend.models import Shop, ShopImage, Package
from backend.database import SessionLocal, init_db, close_engine
from pypinyin import pinyin, Style
from faker import Faker
from sqlalchemy.sql import text
import random
import asyncio

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

# 示例套餐内容
package_contents = [
    "包含：主菜+饮品",
    "包含：双人套餐+甜点",
    "包含：单人餐+小份沙拉",
    "包含：饮品+小吃",
    "包含：三人套餐+汤"
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

async def generate_fake_data_async():
    # 确保数据库表已创建
    await init_db()

    db: Session = SessionLocal()
    try:
        # 禁用外键约束
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        # 清空表
        db.execute(text("TRUNCATE TABLE shop_images;"))
        db.execute(text("TRUNCATE TABLE shops;"))
        db.execute(text("TRUNCATE TABLE search_history;"))
        db.execute(text("TRUNCATE TABLE packages;"))
        
        # 验证是否清空成功
        shop_count = db.execute(text("SELECT COUNT(*) FROM shops;")).scalar()
        package_count = db.execute(text("SELECT COUNT(*) FROM packages;")).scalar()
        if shop_count != 0 or package_count != 0:
            raise RuntimeError(f"Failed to truncate tables: shops={shop_count}, packages={package_count}")
        
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

            # 为每个商家生成至少三张图片
            num_images = random.randint(3, 5)
            for j in range(num_images):
                shop_image = ShopImage(
                    shop_id=shop.id,
                    image_url=random.choice(sample_images)
                )
                db.add(shop_image)

            # 为每个商家生成 1-3 个团购套餐
            num_packages = random.randint(1, 3)
            for k in range(num_packages):
                package = Package(
                    title=f"{shop.category}套餐-{k+1}",
                    price=round(random.uniform(10, 100), 2),
                    description=f"{shop.category}特色套餐，适合{k+1}人享用",
                    contents=random.choice(package_contents),
                    sales=random.randint(0, 200),
                    shop_id=shop.id
                )
                db.add(package)

            print(f"Added shop: {shop.name} with pinyin: {shop.name_pinyin}, category: {shop.category}, category_pinyin: {shop.category_pinyin}, {num_images} images, {num_packages} packages")

        db.commit()

        # 验证插入结果
        shop_count = db.execute(text("SELECT COUNT(*) FROM shops;")).scalar()
        package_count = db.execute(text("SELECT COUNT(*) FROM packages;")).scalar()
        print(f"Successfully inserted {shop_count} shops and {package_count} packages.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()
        # 清理异步引擎
        await close_engine()

if __name__ == "__main__":
    asyncio.run(generate_fake_data_async())