INSERT INTO shops (name, category, rating, price_range, avg_cost, address, phone, business_hours, image_url)
VALUES
    ('火锅大师', '火锅', 4.5, '￥50-100', 75.0, 'XX路123号', '123-456-7890', '10:00-22:00', 'https://via.placeholder.com/300?text=Hotpot'),
    ('奶茶小屋', '奶茶', 4.0, '￥10-50', 20.0, 'YY街456号', '987-654-3210', '09:00-21:00', 'https://via.placeholder.com/300?text=MilkTea'),
    ('炸鸡乐园', '炸鸡', 4.2, '￥10-50', 30.0, 'ZZ街789号', '456-123-7890', '11:00-23:00', 'https://via.placeholder.com/300?text=FriedChicken')
ON DUPLICATE KEY UPDATE name=name;