-- 创建表（如果不存在）
CREATE TABLE IF NOT EXISTS shops (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(50) NOT NULL,
    rating FLOAT,
    price_range VARCHAR(20),
    avg_cost FLOAT,
    address VARCHAR(200),
    phone VARCHAR(20),
    business_hours VARCHAR(50),
    image_url VARCHAR(255)
);

-- 插入数据（如果已存在则更新）
INSERT INTO shops (name, category, rating, price_range, avg_cost, address, phone, business_hours, image_url)
VALUES
    ('火锅大师', '火锅', 4.5, '￥50-100', 75.0, 'XX路123号', '123-456-7890', '10:00-22:00', 'https://via.placeholder.com/300?text=Hotpot'),
    ('奶茶小屋', '奶茶', 4.0, '￥10-50', 20.0, 'YY街456号', '987-654-3210', '09:00-21:00', 'https://via.placeholder.com/300?text=MilkTea'),
    ('炸鸡乐园', '炸鸡', 4.2, '￥10-50', 30.0, 'ZZ街789号', '456-123-7890', '11:00-23:00', 'https://via.placeholder.com/300?text=FriedChicken')
ON DUPLICATE KEY UPDATE
    category = VALUES(category),
    rating = VALUES(rating),
    price_range = VALUES(price_range),
    avg_cost = VALUES(avg_cost),
    address = VALUES(address),
    phone = VALUES(phone),
    business_hours = VALUES(business_hours),
    image_url = VALUES(image_url);