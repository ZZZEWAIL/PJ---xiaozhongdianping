# 小众点评 (Xiaozhong Dianping)
**这是一个餐厅点评系统，实现了用户登录、登出，商家展示，领取、使用优惠券，进行商家点评功能。**

## 部署步骤
1. 安装依赖：
    pip install -r requirements.txt
2. 运行启动脚本：
    ./start.sh

### 验证数据库表
**在远程环境中，登录到数据库并检查表是否正确创建：**
    mysql -u testuser -p -h 127.0.0.1 -P 3306 testdb
    SHOW TABLES;
