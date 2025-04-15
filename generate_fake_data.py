# from sqlalchemy.orm import Session
# from backend.models import Shop, ShopImage
# from backend.database import SessionLocal
# from pypinyin import pinyin, Style
# from faker import Faker
# from sqlalchemy.sql import text
# import random

# # 初始化 Faker，设置中文语言
# fake = Faker('zh_CN')

# # 分类列表
# categories = ["火锅", "奶茶", "海鲜", "烧烤", "川菜", "粤菜", "甜品", "快餐", "日料", "韩料"]

# def generate_fake_shops_and_images():
#     db: Session = SessionLocal()
#     try:
#         # 禁用外键约束
#         db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
#         # 清空表
#         db.execute(text("TRUNCATE TABLE shop_images;"))
#         db.execute(text("TRUNCATE TABLE shops;"))
#         db.execute(text("TRUNCATE TABLE search_history;"))
        
#         # 重新启用外键约束
#         db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
#         db.commit()

#         # 生成 50 个商家
#         for i in range(50):
#             # 随机生成商家名称（2-4 个中文字符）
#             shop_name = fake.company_prefix() + random.choice(["店", "馆", "屋", "大师", "之家"])
            
#             # 转换为拼音（无音调）
#             pinyin_list = pinyin(shop_name, style=Style.NORMAL)
#             name_pinyin = ' '.join([item[0] for item in pinyin_list])

#             # 随机生成其他字段
#             category = random.choice(categories)
#             # 转换为类别拼音（无音调）
#             category_pinyin_list = pinyin(category, style=Style.NORMAL)
#             category_pinyin = ' '.join([item[0] for item in category_pinyin_list])

#             rating = round(random.uniform(3.0, 5.0), 1)
#             avg_cost = round(random.uniform(10, 150), 2)
#             price_range = f"¥{int(avg_cost * 0.8)}-{int(avg_cost * 1.2)}"
#             address = fake.address()
#             phone = fake.phone_number()
#             business_hours = f"{random.randint(8, 11)}:00-{random.randint(20, 23)}:00"
#             image_url = None

#             # 创建商家（使用 ORM）
#             shop = Shop(
#                 name=shop_name,
#                 category=category,
#                 rating=rating,
#                 price_range=price_range,
#                 avg_cost=avg_cost,
#                 name_pinyin=name_pinyin,
#                 category_pinyin=category_pinyin,  # 新增
#                 address=address,
#                 phone=phone,
#                 business_hours=business_hours,
#                 image_url=image_url
#             )
#             db.add(shop)
#             db.flush()  # 确保 shop.id 生成

#             # 为每个商家生成 1-3 张图片
#             num_images = random.randint(1, 3)
#             for j in range(num_images):
#                 shop_image = ShopImage(
#                     shop_id=shop.id,
#                     image_url=f"https://example.com/shop_{shop.id}_image_{j}.jpg"
#                 )
#                 db.add(shop_image)

#             print(f"Added shop: {shop.name} with pinyin: {shop.name_pinyin}, category: {shop.category}, category_pinyin: {shop.category_pinyin}, {num_images} images")

#         db.commit()
#     except Exception as e:
#         print(f"Error: {e}")
#         db.rollback()
#     finally:
#         db.close()

# if __name__ == "__main__":
#     generate_fake_shops_and_images()

from sqlalchemy.orm import Session
from backend.models import Shop, ShopImage
from backend.database import SessionLocal
from pypinyin import pinyin, Style
from faker import Faker
import random
from sqlalchemy.sql import text
from sqlalchemy.sql import text  # 确保导入 text

# 初始化 Faker，设置中文语言
fake = Faker('zh_CN')

# 分类列表
categories = ["火锅", "奶茶", "海鲜", "烧烤", "川菜", "粤菜", "甜品", "快餐", "日料", "韩料"]

def generate_fake_shops_and_images():
    db: Session = SessionLocal()
    try:
        # 禁用外键约束
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        
        # 清空表
        db.execute(text("TRUNCATE TABLE shop_images;"))
        db.execute(text("TRUNCATE TABLE shops;"))
        db.execute(text("TRUNCATE TABLE search_history;"))
        
        # 重新启用外键约束
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()

        # 生成 50 个商家
        for i in range(50):
            # 随机生成商家名称（2-4 个中文字符）
            shop_name = fake.company_prefix() + random.choice(["店", "馆", "屋", "大师", "之家"])
            
            # 转换为拼音（无音调）
            pinyin_list = pinyin(shop_name, style=Style.NORMAL)
            name_pinyin = ' '.join([item[0] for item in pinyin_list])

            # 随机生成其他字段
            category = random.choice(categories)
            # 转换为类别拼音（无音调）
            category_pinyin_list = pinyin(category, style=Style.NORMAL)
            category_pinyin = ' '.join([item[0] for item in category_pinyin_list])

            rating = round(random.uniform(3.0, 5.0), 1)
            avg_cost = round(random.uniform(10, 150), 2)
            price_range = f"¥{int(avg_cost * 0.8)}-{int(avg_cost * 1.2)}"
            address = fake.address()
            phone = fake.phone_number()
            business_hours = f"{random.randint(8, 11)}:00-{random.randint(20, 23)}:00"
            image_url = None

            # 检查是否存在重复记录
            existing_shop = db.query(Shop).filter(Shop.name == shop_name).first()
            if existing_shop:
                # 更新记录
                existing_shop.category = category
                existing_shop.rating = rating
                existing_shop.price_range = price_range
                existing_shop.avg_cost = avg_cost
                existing_shop.name_pinyin = name_pinyin
                existing_shop.category_pinyin = category_pinyin
                existing_shop.address = address
                existing_shop.phone = phone
                existing_shop.business_hours = business_hours
                existing_shop.image_url = image_url
                print(f"Updated shop: {shop_name}")
            else:
                # 插入新记录
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
                    image_url=image_url
                )
                db.add(shop)
                db.flush()  # 确保 shop.id 生成

                # 为每个商家生成 1-3 张图片
                num_images = random.randint(1, 3)
                for j in range(num_images):
                    shop_image = ShopImage(
                        shop_id=shop.id,
                        image_url=f"https://example.com/shop_{shop.id}_image_{j}.jpg"
                    )
                    db.add(shop_image)

                print(f"Inserted shop: {shop_name} with pinyin: {name_pinyin}, category: {category}, category_pinyin: {category_pinyin}")

        db.commit()
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_fake_shops_and_images()