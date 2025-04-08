# 小众点评 (Xiaozhong Dianping)
**lab2 阶段：这是一个基于 FastAPI 和前端技术实现的点评网站，支持用户认证和商家搜索功能。**

**连接 Aiven MySQL**
    mysql -h xiaozhongdianping-xiaozhongdianping.h.aivencloud.com -P 14983 -u avnadmin -p
**远程数据库连接失败**
    更改为本地数据库：
SQLALCHEMY_DATABASE_URL = "mysql+aiomysql://testuser:testpassword@127.0.0.1:3306/testdb"

**部署步骤**
1. 安装依赖：
    pip install -r requirements.txt
2. 运行启动脚本：
    ./start.sh
**验证数据库表**
在远程环境中，登录到数据库并检查表是否正确创建：
mysql -u testuser -p -h 127.0.0.1 -P 3306 testdb
SHOW TABLES;
**测试商家搜索功能中的 排序逻辑** 
**API端点：/shops/search**
pytest tests/test_filter_sort.py -v