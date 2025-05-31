# Lab 4新增API
- 基于"邀请下单"和"点评功能"的需求。
- 文档包括:接口地址与请求方式、接口名称与功能描述、请求体与响应体结构、请求示例与响应示例以及异常 API 调用。


### 1. 获取用户邀请码
- **接口地址**: `/api/invitation/code`
- **请求方式**: GET
- **接口名称**: 获取邀请码
- **功能描述**: 获取当前登录用户的唯一邀请码，若用户尚未拥有邀请码，则自动生成一个6位随机字母数字组合的邀请码并绑定。

##### 请求体
- 无请求参数

##### 响应体
| 字段名   | 数据类型 | 是否必填 | 说明               |
|----------|----------|----------|--------------------|
| code     | string   | 是       | 用户的邀请码       |
| message  | string   | 是       | 操作状态信息       |

##### 请求示例
```
GET /api/invitation/code
Authorization: Bearer <token>
```

##### 响应示例（成功）
```json
{
  "code": "A1B2C3",
  "message": "Success"
}
```

##### 异常 API 调用
- **错误码**: 401 Unauthorized
- **描述**: 用户未登录或 token 无效
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "Not authenticated"
  }
  ```
- **错误码**: 404 Not Found
- **描述**: 用户不存在
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "用户不存在"
  }
  ```

#### 2. 获取邀请记录
- **接口地址**: `/api/invitation/records`
- **请求方式**: GET
- **接口名称**: 获取邀请记录
- **功能描述**: 查询当前登录用户作为邀请人成功邀请的新用户记录，包括被邀请用户ID、用户名、下单时间和实付金额。

##### 请求体
- 无请求参数

##### 响应体
| 字段名       | 数据类型 | 是否必填 | 说明                     |
|--------------|----------|----------|--------------------------|
| records      | array    | 是       | 邀请记录列表             |
| total_invited| integer  | 是       | 有效邀请的总次数         |
| records[].user_id | integer | 是     | 被邀请用户ID             |
| records[].username | string  | 是     | 被邀请用户的用户名       |
| records[].order_time | string | 是     | 下单时间（ISO格式）      |
| records[].amount | float   | 是     | 订单实付金额             |

##### 请求示例
```
GET /api/invitation/records
Authorization: Bearer <token>
```

##### 响应示例（成功）
```json
{
  "records": [
    {
      "user_id": 2,
      "username": "Bob",
      "order_time": "2025-05-24T20:00:00Z",
      "amount": 15.50
    }
  ],
  "total_invited": 1
}
```

##### 异常 API 调用
- **错误码**: 401 Unauthorized
- **描述**: 用户未登录或 token 无效
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

---

#### 3. 创建订单（有修改）
- **接口地址**: `/api/orders`
- **请求方式**: POST
- **接口名称**: 创建订单
- **功能描述**: 用户创建订单，可选择使用优惠券或填写邀请码，订单创建后记录邀请信息（如适用）并触发相关通知。

##### 请求体
| 字段名         | 数据类型 | 是否必填 | 说明                       |
|----------------|----------|----------|----------------------------|
| package_id     | integer  | 是       | 套餐ID                     |
| coupon_id      | integer  | 否       | 优惠券ID（可选）           |
| invitation_code| string   | 否       | 邀请码（可选）             |

##### 响应体
| 字段名       | 数据类型 | 是否必填 | 说明                     |
|--------------|----------|----------|--------------------------|
| id           | integer  | 是       | 订单ID                   |
| voucher_code | string   | 是       | 订单券码（16位数字）     |
| order_amount | float    | 是       | 订单实付金额             |
| created_at   | string   | 是       | 订单创建时间（ISO格式）  |

##### 请求示例
```json
POST /api/orders
Authorization: Bearer <token>
{
  "package_id": 1,
  "coupon_id": 1,
  "invitation_code": "A1B2C3"
}
```

##### 响应示例（成功）
```json
{
  "id": 1,
  "voucher_code": "1234567890123456",
  "order_amount": 45.67,
  "created_at": "2025-05-24T20:00:00Z"
}
```

##### 异常 API 调用
- **错误码**: 400 Bad Request
- **描述**: 无效邀请码
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "无效的邀请码"
  }
  ```
- **错误码**: 400 Bad Request
- **描述**: 仅首次下单可使用邀请码
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "仅首次下单可使用邀请码"
  }
  ```
- **错误码**: 400 Bad Request
- **描述**: 订单金额需超过10元
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "订单金额需超过10元"
  }
  ```
- **错误码**: 404 Not Found
- **描述**: 未找到指定套餐
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "未找到指定套餐"
  }
  ```
- **错误码**: 401 Unauthorized
- **描述**: 用户未登录或 token 无效
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

---

## 点评功能相关API

### 4. 获取商家点评
- **接口地址**: `/api/shops/{shop_id}/reviews`
- **请求方式**: GET
- **接口名称**: 获取商家点评列表
- **功能描述**: 分页获取指定商家的点评列表，支持排序和筛选，包含多级嵌套回复。

##### 请求参数
| 参数名   | 数据类型 | 是否必填 | 说明                                    |
|----------|----------|----------|-----------------------------------------|
| shop_id  | integer  | 是       | 商家ID（路径参数）                      |
| page     | integer  | 否       | 页码，默认为1                           |
| limit    | integer  | 否       | 每页数量，默认为10，最大100             |
| sort     | string   | 否       | 排序方式：newest（最新，默认）、oldest（最早） |

##### 响应体
| 字段名           | 数据类型 | 是否必填 | 说明                        |
|------------------|----------|----------|-----------------------------|
| reviews          | array    | 是       | 点评列表                    |
| total            | integer  | 是       | 总点评数                    |
| page             | integer  | 是       | 当前页码                    |
| limit            | integer  | 是       | 每页数量                    |
| has_more         | boolean  | 是       | 是否还有更多数据            |
| reviews[].id     | integer  | 是       | 点评ID                      |
| reviews[].user_id| integer  | 是       | 用户ID                      |
| reviews[].username| string  | 是       | 用户名                      |
| reviews[].content| string   | 是       | 点评内容                    |
| reviews[].created_at| string| 是       | 创建时间（ISO格式）         |
| reviews[].replies| array    | 是       | 回复列表                    |

##### 请求示例
```
GET /api/shops/1/reviews?page=1&limit=10&sort=newest
Authorization: Bearer <token>
```

##### 响应示例（成功）
```json
{
  "reviews": [
    {
      "id": 1,
      "user_id": 1,
      "username": "用户A",
      "content": "这家店的套餐很不错，分量足味道好，性价比很高。汉堡肉饼很厚实，薯条也很脆。",
      "created_at": "2025-05-24T18:30:00Z",
      "replies": [
        {
          "id": 1,
          "user_id": 2,
          "username": "用户B",
          "content": "同意！我也觉得很好吃，特别是他们的招牌汉堡",
          "created_at": "2025-05-24T19:00:00Z",
          "parent_id": null
        }
      ]
    }
  ],
  "total": 25,
  "page": 1,
  "limit": 10,
  "has_more": true
}
```

##### 异常 API 调用
- **错误码**: 404 Not Found
- **描述**: 商家不存在
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "商家不存在"
  }
  ```
- **错误码**: 401 Unauthorized
- **描述**: 用户未登录或 token 无效
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

### 5. 创建商家点评
- **接口地址**: `/api/shops/{shop_id}/reviews`
- **请求方式**: POST
- **接口名称**: 创建商家点评
- **功能描述**: 用户对指定商家发表点评，自动检查奖励券发放条件（3条15字以上点评可获得8折优惠券）。

##### 请求参数
| 参数名   | 数据类型 | 是否必填 | 说明                  |
|----------|----------|----------|-----------------------|
| shop_id  | integer  | 是       | 商家ID（路径参数）    |

##### 请求体
| 字段名   | 数据类型 | 是否必填 | 说明                           |
|----------|----------|----------|--------------------------------|
| content  | string   | 是       | 点评内容，长度15-500字符       |

##### 响应体
| 字段名          | 数据类型 | 是否必填 | 说明                        |
|-----------------|----------|----------|-----------------------------|
| review          | object   | 是       | 创建的点评信息              |
| reward          | object   | 否       | 奖励券信息（满足条件时返回）|
| message         | string   | 是       | 操作结果信息                |
| review.id       | integer  | 是       | 点评ID                      |
| review.user_id  | integer  | 是       | 用户ID                      |
| review.username | string   | 是       | 用户名                      |
| review.content  | string   | 是       | 点评内容                    |
| review.created_at| string  | 是       | 创建时间（ISO格式）         |
| reward.coupon_name| string | 否       | 优惠券名称                  |
| reward.coupon_value| string| 否       | 优惠券价值描述              |
| reward.expiry_days| integer| 否       | 有效天数                    |

##### 请求示例
```json
POST /api/shops/1/reviews
Authorization: Bearer <token>
{
  "content": "这家店的服务很好，环境也不错，菜品味道很棒，下次还会再来的！"
}
```

##### 响应示例（成功，含奖励）
```json
{
  "review": {
    "id": 26,
    "user_id": 1,
    "username": "TestUser",
    "content": "这家店的服务很好，环境也不错，菜品味道很棒，下次还会再来的！",
    "created_at": "2025-05-24T20:15:30Z",
    "replies": []
  },
  "reward": {
    "coupon_name": "8折优惠券",
    "coupon_value": "最高减20元",
    "expiry_days": 7
  },
  "message": "点评发布成功"
}
```

##### 响应示例（成功，无奖励）
```json
{
  "review": {
    "id": 27,
    "user_id": 1,
    "username": "TestUser",
    "content": "这家店的服务很好，环境也不错，菜品味道很棒，下次还会再来的！",
    "created_at": "2025-05-24T20:16:45Z",
    "replies": []
  },
  "reward": null,
  "message": "点评发布成功"
}
```

##### 异常 API 调用
- **错误码**: 400 Bad Request
- **描述**: 点评内容不符合要求
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "点评内容不能少于15个字符"
  }
  ```
- **错误码**: 404 Not Found
- **描述**: 商家不存在
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "商家不存在"
  }
  ```
- **错误码**: 401 Unauthorized
- **描述**: 用户未登录或 token 无效
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

### 6. 回复点评
- **接口地址**: `/api/reviews/{review_id}/replies`
- **请求方式**: POST
- **接口名称**: 回复点评
- **功能描述**: 用户对指定点评进行回复，支持多级嵌套回复结构。

##### 请求参数
| 参数名    | 数据类型 | 是否必填 | 说明                  |
|-----------|----------|----------|-----------------------|
| review_id | integer  | 是       | 点评ID（路径参数）    |

##### 请求体
| 字段名   | 数据类型 | 是否必填 | 说明                     |
|----------|----------|----------|--------------------------|
| content  | string   | 是       | 回复内容，不能为空       |

##### 响应体
| 字段名          | 数据类型 | 是否必填 | 说明                    |
|-----------------|----------|----------|-------------------------|
| reply           | object   | 是       | 创建的回复信息          |
| message         | string   | 是       | 操作结果信息            |
| reply.id        | integer  | 是       | 回复ID                  |
| reply.user_id   | integer  | 是       | 用户ID                  |
| reply.username  | string   | 是       | 用户名                  |
| reply.content   | string   | 是       | 回复内容                |
| reply.created_at| string   | 是       | 创建时间（ISO格式）     |
| reply.parent_id | integer  | 是       | 父级点评ID              |

##### 请求示例
```json
POST /api/reviews/1/replies
Authorization: Bearer <token>
{
  "content": "我也有同样的感受，这家店确实不错！"
}
```

##### 响应示例（成功）
```json
{
  "reply": {
    "id": 5,
    "user_id": 1,
    "username": "TestUser",
    "content": "我也有同样的感受，这家店确实不错！",
    "created_at": "2025-05-24T20:25:15Z",
    "parent_id": 1
  },
  "message": "回复发布成功"
}
```

##### 异常 API 调用
- **错误码**: 400 Bad Request
- **描述**: 回复内容不能为空
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "回复内容不能为空"
  }
  ```
- **错误码**: 404 Not Found
- **描述**: 点评不存在
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "点评不存在"
  }
  ```
- **错误码**: 401 Unauthorized
- **描述**: 用户未登录或 token 无效
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

### 7. 获取用户点评记录
- **接口地址**: `/api/user/reviews`
- **请求方式**: GET
- **接口名称**: 获取用户点评记录
- **功能描述**: 分页获取当前用户的点评历史记录，按创建时间倒序排列。

##### 请求参数
| 参数名   | 数据类型 | 是否必填 | 说明                      |
|----------|----------|----------|---------------------------|
| page     | integer  | 否       | 页码，默认为1             |
| limit    | integer  | 否       | 每页数量，默认为10，最大50|

##### 响应体
| 字段名           | 数据类型 | 是否必填 | 说明                    |
|------------------|----------|----------|-------------------------|
| reviews          | array    | 是       | 用户点评列表            |
| total            | integer  | 是       | 用户总点评数            |
| page             | integer  | 是       | 当前页码                |
| limit            | integer  | 是       | 每页数量                |
| reviews[].id     | integer  | 是       | 点评ID                  |
| reviews[].shop_id| integer  | 是       | 商家ID                  |
| reviews[].shop_name| string | 是       | 商家名称                |
| reviews[].content| string   | 是       | 点评内容                |
| reviews[].created_at| string| 是       | 创建时间（ISO格式）     |

##### 请求示例
```
GET /api/user/reviews?page=1&limit=5
Authorization: Bearer <token>
```

##### 响应示例（成功）
```json
{
  "reviews": [
    {
      "id": 26,
      "shop_id": 1,
      "shop_name": "美味汉堡店",
      "content": "这家店的服务很好，环境也不错，菜品味道很棒，下次还会再来的！",
      "created_at": "2025-05-24T20:15:30Z"
    },
    {
      "id": 15,
      "shop_id": 2,
      "shop_name": "咖啡小屋",
      "content": "咖啡很香醇，环境很舒适，适合工作和聊天，推荐他们的拿铁和提拉米苏。",
      "created_at": "2025-05-23T16:20:45Z"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 5
}
```

##### 异常 API 调用
- **错误码**: 401 Unauthorized
- **描述**: 用户未登录或 token 无效
- **响应体结构**:
  | 字段名   | 数据类型 | 是否必填 | 说明         |
  |----------|----------|----------|--------------|
  | detail   | string   | 是       | 错误描述     |
- **响应示例**:
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

---

### 注意事项
- 所有接口需携带 `Authorization: Bearer <token>` 头以验证用户身份。
- 文档基于 Lab 4 新增接口，未包含之前 Lab 的内容。
- 异常处理涵盖常见场景，确保用户友好。
