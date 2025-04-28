
# 为了方便团队开发，以下是提供的信息清单，涵盖后端 API、前端集成、环境配置和测试方法等方面：

### 1. API 

#### **1.1 API 端点概览**
- **登录相关**：
  - `POST /auth/login`
    - **功能**：用户登录，生成 `access_token` 并设置 Cookie。
    - **请求**：
      ```json
      {
        "username": "string",
        "password": "string"
      }
      ```
    - **响应**（`200 OK`）：
      ```json
      {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer"
      }
      ```
    - **Cookie**：设置 `access_token`（`httponly`, `secure=False`, `samesite="Lax"`, `path="/"`, 有效期 30 分钟）。
  - `POST /auth/logout`
    - **功能**：用户登出，清除 `access_token` Cookie。
    - **响应**（`200 OK`）：
      ```json
      {
        "message": "Logged out successfully"
      }
      ```
  - `GET /auth/protected-endpoint`
    - **功能**：验证用户是否登录，返回用户信息。
    - **认证**：需要 `access_token` Cookie。
    - **响应**（`200 OK`）：
      ```json
      {
        "username": "Alice",
        "id": 1
      }
      ```
    - **错误**（`401 Unauthorized`）：
      ```json
      {
        "detail": "Not authenticated"
      }
      ```

- **订单相关**：
  - `GET /api/orders/{order_id}`
    - **功能**：获取指定订单详情。
    - **认证**：需要 `access_token` Cookie。
    - **路径参数**：
      - `order_id`：订单 ID（整数）。
    - **响应示例**（`200 OK`）：
      ```json
      {
        "package_title": "火锅套餐-1",
        "created_at": "2025-04-27T10:30:00",
        "shop_name": "张大师店",
        "voucher_code": "1234567890123456"
      }
      ```
    - **错误**（`401 Unauthorized`）：
      ```json
      {
        "detail": "Not authenticated"
      }
      ```
  - `GET /api/user/orders`
    - **功能**：获取当前用户的订单列表（分页）。
    - **认证**：需要 `access_token` Cookie。
    - **查询参数**：
      - `page`：页码（默认 1）。
      - `page_size`：每页条数（默认 10）。
    - **响应**（`200 OK`）：
      ```json
      {
        "total": 1,
        "page": 1,
        "page_size": 10,
        "data": [
          {
            "package_title": "火锅套餐-1",
            "created_at": "2025-04-27T10:30:00",
            "shop_name": "张大师店",
            "voucher_code": null
          }
        ]
      }
      ```

- **店铺相关**（无需认证）：
  - `GET /api/shops/{shop_id}/packages`
    - **功能**：获取指定店铺的套餐列表。
    - **路径参数**：
      - `shop_id`：店铺 ID（整数）。
    - **响应示例**（`200 OK`）：
      ```json
      [
        {
          "id": 1,
          "title": "火锅套餐-1",
          "price": 45.67,
          "description": "火锅特色套餐，适合1人享用",
          "contents": "包含：主菜+饮品",
          "sales": 120
        },
        {
          "id": 2,
          "title": "火锅套餐-2",
          "price": 78.90,
          "description": "火锅特色套餐，适合2人享用",
          "contents": "包含：双人套餐+甜点",
          "sales": 80
        }
      ]
      ```

#### **1.2 认证方式**
- 使用 JWT（JSON Web Token）进行认证。
- `access_token` 存储在 HTTP-only Cookie 中：
  - 键：`access_token`
  - 属性：`httponly=True`, `secure=False`（开发环境）, `samesite="Lax"`, `path="/"`
  - 有效期：30 分钟
- 所有需要认证的接口（如 `/api/orders/{order_id}`）需在请求中携带 `access_token` Cookie。

#### **1.3 Swagger UI**
- Swagger UI 地址，方便查看和测试 API：
  ```
  http://127.0.0.1:8000/docs
  ```
- 说明如何使用：
  1. 打开 Swagger UI。
  2. 先调用 `POST /auth/login` 登录（例如 `username: Alice`, `password: test111`）。
  3. 测试其他接口，Swagger UI 会自动携带 `access_token` Cookie。

---

### 2. 环境配置
帮助团队成员快速搭建开发环境。

#### **2.1 依赖安装**
- **Python 依赖**：
  - 提供 `requirements.txt` 文件：
    ```
    fastapi==0.110.0
    uvicorn==0.29.0
    sqlalchemy[asyncio]==2.0.29
    asyncpg==0.29.0
    bcrypt==4.1.2
    pyjwt==2.8.0
    python-dotenv==1.0.1
    ```
  - 安装命令：
    ```bash
    pip install -r requirements.txt
    ```
- **前端依赖**：
  - 说明前端使用的库（如 Bootstrap）：
    ```html
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    ```
  - 如果有 Node.js 依赖，提供 `package.json`。

#### **2.2 环境变量**
- `.env` 文件模板：
  ```
  SECRET_KEY=19deaf635606f544216477efcfd68a33fe63bfdd31755348174f607b6b2ae545
  DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/dbname
  ```
- **说明**：
  - `SECRET_KEY` 用于 JWT 签名，生产环境中应更换。
  - `DATABASE_URL` 根据实际数据库配置修改。

#### **2.3 数据库配置**
- **数据库**：PostgreSQL
- **表结构**：
  - `users` 表：
    ```
    id | username | password_hash | created_at | last_login
    1  | Alice    | $2b$12$YOUR_HASHED_PASSWORD | 2025-04-27 10:00:00 | NULL
    ```
  - `orders` 表：
    ```
    id | user_id | package_id | voucher_code     | coupon_id | order_amount | created_at
    1  | 1       | 1          | 1234567890123456 | NULL      | 50           | 2025-04-27 10:30:00
    ```
- **初始化数据**：
  - 提供 SQL 脚本：
    ```sql
    INSERT INTO users (id, username, password_hash, created_at)
    VALUES (1, 'Alice', '$2b$12$YOUR_HASHED_PASSWORD', '2025-04-27 10:00:00');

    INSERT INTO orders (id, user_id, package_id, voucher_code, order_amount, created_at)
    VALUES (1, 1, 1, '1234567890123456', 50, '2025-04-27 10:30:00');
    ```

#### **2.4 启动服务**
- **后端**：
  - 启动命令：
    ```bash
    ./start.sh
    ```
- **前端**：
  - 如何运行前端（例如使用 VS Code 的 Live Server 插件）：
    1. 打开 `login.html`。
    2. 使用 Live Server 启动（默认端口可能为 5500）。

---

### 3. 前端集成说明
帮助前端开发人员快速集成 API。

#### **3.1 登录流程**
- **步骤**：
  1. 用户在 `login.html` 输入用户名和密码。
  2. 调用 `POST /auth/login`，获取 `access_token`（自动设置在 Cookie 中）。
  3. 跳转到 `index.html`，调用 `GET /auth/protected-endpoint` 验证登录状态。
- **代码示例**（`login.js` 已提供）：
  ```javascript
  const response = await fetch('http://127.0.0.1:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
      credentials: 'include',
  });
  ```

#### **3.2 调用受保护的接口**
- **示例**：获取订单详情（`GET /api/orders/{order_id}`）：
  ```javascript
  async function getOrder(orderId) {
      try {
          const response = await fetch(`http://127.0.0.1:8000/api/orders/${orderId}`, {
              method: 'GET',
              credentials: 'include',
          });
          if (response.ok) {
              const data = await response.json();
              console.log('Order details:', data);
          } else {
              console.error('Failed to fetch order:', response.status);
              alert('请先登录');
              window.location.href = 'login.html';
          }
      } catch (error) {
          console.error('Error:', error);
          alert('网络错误，请稍后重试');
      }
  }
  ```

#### **3.3 登出**
- 调用 `POST /auth/logout`，清除 Cookie 并跳转：
  ```javascript
  const response = await fetch('http://127.0.0.1:8000/auth/logout', {
      method: 'POST',
      credentials: 'include',
  });
  if (response.ok) {
      window.location.href = 'login.html';
  }
  ```

---

### 4. 测试方法

#### **4.1 Swagger UI 测试**
- 地址：`http://127.0.0.1:8000/docs`
- **步骤**：
  1. 启动后端服务。
  2. 打开 Swagger UI。
  3. 调用 `POST /auth/login` 登录（`Alice`, `test111`）。
  4. 测试其他接口（如 `GET /api/orders/1`）。

#### **4.2 前端测试**
- 打开 `login.html`，登录后确认跳转到 `index.html`。
- 访问订单详情页面（如果已开发），调用 `GET /api/orders/{order_id}`。

---

### 5. 已知问题和注意事项
- **开发环境**：
  - `secure=False`，生产环境需启用 HTTPS 并设为 `True`。
  - `samesite="Lax"`，生产环境建议改为 `Strict`。
- **token 有效期**：
  - 目前为 30 分钟，未实现刷新 token 机制。
  - 建议开发刷新 token 端点。
- **错误处理**：
  - 前端遇到 `401` 时会跳转到登录页面，可优化为显示提示。


### 6. 后续开发建议

