from faker import Faker
import random
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 初始化 Faker
fake = Faker()

# 数据库连接字符串
DATABASE_URL = os.getenv("DATABASE_URL").replace("+aiomysql", "+pymysql")
engine = create_engine(DATABASE_URL)

def generate_fake_shops(num_shops=20):
    """生成伪商家数据"""
    shops = []
    categories = ["火锅", "奶茶", "烧烤", "西餐", "快餐", "甜品"]
    for _ in range(num_shops):
        shop = {
            "name": fake.company(),
            "category": random.choice(categories),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "price_range": f"￥{random.randint(10, 50)}-{random.randint(51, 200)}",
            "avg_cost": round(random.uniform(20.0, 150.0), 2),
            "address": fake.address(),
            "phone": fake.phone_number()[:20],  # 限制电话号码长度为 20
            "business_hours": "10:00-22:00",
            "image_url": fake.image_url()
        }
        shops.append(shop)
    return shops

def insert_fake_shops(shops):
    """将伪商家数据插入数据库"""
    with engine.connect() as conn:
        for shop in shops:
            conn.execute(text("""
                INSERT INTO shops (name, category, rating, price_range, avg_cost, address, phone, business_hours, image_url)
                VALUES (:name, :category, :rating, :price_range, :avg_cost, :address, :phone, :business_hours, :image_url)
                ON DUPLICATE KEY UPDATE
                category = VALUES(category),
                rating = VALUES(rating),
                image_url = VALUES(image_url)
            """), shop)
        conn.commit()

if __name__ == "__main__":
    fake_shops = generate_fake_shops(20)
    insert_fake_shops(fake_shops)
    print("伪商家数据已成功插入数据库！")