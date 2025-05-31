"""
Mock API Server for 小众点评 Frontend Development
提供前端开发所需的Mock API接口

@author Frontend Team
@version 1.0
"""

from fastapi import FastAPI, HTTPException, Request, Response, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import json

app = FastAPI(title="小众点评 Mock API", version="1.0.0")

# ==================== 数据模型 ====================

class InvitationCode(BaseModel):
    code: str
    message: str = "Success"

class InvitationRecord(BaseModel):
    user_id: int
    username: str
    order_time: str
    amount: float

class InvitationRecordsResponse(BaseModel):
    records: List[InvitationRecord]
    total_invited: int

class Package(BaseModel):
    id: int
    title: str
    price: float
    description: str
    contents: str
    sales: int

class Coupon(BaseModel):
    name: str
    discount_type: str
    discount_value: float
    description: str
    max_discount: Optional[float] = None

class CouponInfo(BaseModel):
    id: int
    coupon: Coupon
    expiry_date: str

class OrderRequest(BaseModel):
    package_id: int
    coupon_id: Optional[int] = None
    invitation_code: Optional[str] = None

class OrderResponse(BaseModel):
    id: int
    voucher_code: str
    order_amount: float
    message: str = "Order created successfully"

class Shop(BaseModel):
    id: int
    name: str
    address: str
    phone: str
    description: str
    rating: float
    image_url: str

class Review(BaseModel):
    id: int
    user_id: int
    username: str
    content: str
    created_at: str
    replies: List = []

class ReviewRequest(BaseModel):
    content: str

class ReplyRequest(BaseModel):
    content: str

class UserStatus(BaseModel):
    username: str
    user_id: int
    login_time: str

# ==================== Mock 数据 ====================

# Mock用户数据
mock_user = {
    "user_id": 1,
    "username": "TestUser",
    "login_time": datetime.now().isoformat()
}

# Mock邀请码数据
mock_invitation_codes = {
    1: "ABC123"
}

# Mock邀请记录
mock_invitation_records = [
    {
        "user_id": 2,
        "username": "Alice",
        "order_time": "2025-05-24T20:00:00Z",
        "amount": 15.50
    },
    {
        "user_id": 3,
        "username": "Bob",
        "order_time": "2025-05-23T18:30:00Z",
        "amount": 25.80
    }
]

# Mock套餐数据
mock_packages = {
    1: {
        "id": 1,
        "title": "超值双人套餐",
        "price": 68.00,
        "description": "适合2-3人享用的丰盛套餐，包含招牌菜品",
        "contents": "招牌汉堡*2+薯条*2+可乐*2+鸡翅*4",
        "sales": 156
    },
    2: {
        "id": 2,
        "title": "单人经典套餐", 
        "price": 32.00,
        "description": "一人独享的经典搭配",
        "contents": "经典汉堡*1+薯条*1+可乐*1",
        "sales": 89
    }
}

# Mock优惠券数据
mock_coupons = [
    {
        "id": 1,
        "coupon": {
            "name": "新用户专享券",
            "discount_type": "deduction",
            "discount_value": 10.0,
            "description": "新用户专享10元减免券",
            "max_discount": None
        },
        "expiry_date": "2025-06-30T23:59:59Z"
    },
    {
        "id": 2,
        "coupon": {
            "name": "8折优惠券",
            "discount_type": "discount", 
            "discount_value": 0.8,
            "description": "全场8折优惠，最高减20元",
            "max_discount": 20.0
        },
        "expiry_date": "2025-05-31T23:59:59Z"
    }
]

# Mock商家数据
mock_shops = {
    1: {
        "id": 1,
        "name": "美味汉堡店",
        "address": "北京市朝阳区某某街道123号",
        "phone": "010-12345678",
        "description": "专注美式汉堡20年，新鲜食材，现做现卖",
        "rating": 4.5,
        "image_url": "https://via.placeholder.com/300x200",
    }
}

# Mock点评数据
mock_reviews = [
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
                "parent_id": None
            }
        ]
    },
    {
        "id": 2,
        "user_id": 3,
        "username": "用户C", 
        "content": "环境不错，服务也很好，就是等餐时间有点长。不过食物确实很新鲜。",
        "created_at": "2025-05-23T16:20:00Z",
        "replies": []
    }
]

# ==================== 认证相关 API ====================

@app.get("/auth/status")
async def get_auth_status():
    """获取用户认证状态"""
    return UserStatus(
        username=mock_user["username"],
        user_id=mock_user["user_id"], 
        login_time=mock_user["login_time"]
    )

@app.post("/auth/logout")
async def logout():
    """用户登出"""
    return {"message": "Logged out successfully"}

# ==================== 邀请相关 API ====================

@app.get("/api/invitation/code")
async def get_invitation_code():
    """获取用户邀请码"""
    user_id = mock_user["user_id"]
    code = mock_invitation_codes.get(user_id, "ABC123")
    return InvitationCode(code=code)

@app.get("/api/invitation/records")
async def get_invitation_records():
    """获取邀请记录"""
    return InvitationRecordsResponse(
        records=mock_invitation_records,
        total_invited=len(mock_invitation_records)
    )

@app.post("/api/invitation/verify")
async def verify_invitation_code(code: str):
    """验证邀请码"""
    # Mock验证逻辑
    if code == "SELF01":
        raise HTTPException(status_code=400, detail="不能使用自己的邀请码")
    elif code == "USED01":
        raise HTTPException(status_code=400, detail="您已使用过邀请码，每个用户只能使用一次")
    elif code == "INVALID":
        raise HTTPException(status_code=400, detail="邀请码不存在或已失效")
    elif code in ["ABC123", "DEF456", "GHI789"]:
        return {"valid": True, "message": "邀请码验证成功"}
    else:
        raise HTTPException(status_code=400, detail="邀请码格式错误或不存在")

# ==================== 套餐相关 API ====================

@app.get("/api/packages/{package_id}")
async def get_package_detail(package_id: int):
    """获取套餐详情"""
    if package_id not in mock_packages:
        raise HTTPException(status_code=404, detail="套餐不存在")
    return mock_packages[package_id]

# ==================== 优惠券相关 API ====================

@app.get("/api/user/coupons/available")
async def get_available_coupons(package_id: Optional[int] = None):
    """获取用户可用优惠券"""
    # 可以根据package_id过滤优惠券，这里简单返回所有
    return mock_coupons

@app.get("/api/user/reward-coupons")
async def get_reward_coupons():
    """获取奖励券明细"""
    return {
        "coupons": [
            {
                "id": 1,
                "name": "邀请奖励券",
                "value": 20,
                "type": "fixed",
                "description": "无门槛20元优惠券",
                "issued_date": "2025-05-20T10:30:00Z",
                "expiry_date": "2025-05-27T23:59:59Z",
                "status": "available"
            }
        ]
    }

# ==================== 订单相关 API ====================

@app.post("/api/orders")
async def create_order(order_request: OrderRequest):
    """创建订单"""
    # 验证套餐是否存在
    if order_request.package_id not in mock_packages:
        raise HTTPException(status_code=404, detail="套餐不存在")
    
    package = mock_packages[order_request.package_id]
    order_amount = package["price"]
    
    # 应用优惠券折扣
    if order_request.coupon_id:
        coupon_info = next((c for c in mock_coupons if c["id"] == order_request.coupon_id), None)
        if coupon_info:
            coupon = coupon_info["coupon"]
            if coupon["discount_type"] == "deduction":
                order_amount = max(0, order_amount - coupon["discount_value"])
            elif coupon["discount_type"] == "discount":
                discount = order_amount * (1 - coupon["discount_value"])
                if coupon.get("max_discount"):
                    discount = min(discount, coupon["max_discount"])
                order_amount = order_amount - discount
    
    # 验证邀请码
    if order_request.invitation_code:
        valid_codes = ["ABC123", "DEF456", "GHI789"]
        if order_request.invitation_code not in valid_codes:
            raise HTTPException(status_code=400, detail="邀请码无效")
    
    # 生成订单
    order_id = 1001
    voucher_code = f"V{order_id:06d}"
    
    return OrderResponse(
        id=order_id,
        voucher_code=voucher_code,
        order_amount=order_amount
    )

# ==================== 商家相关 API ====================

@app.get("/api/shops/{shop_id}")
async def get_shop_detail(shop_id: int, image_page:int=1, image_page_size:int=1):
    """获取商家详情"""
    if shop_id not in mock_shops:
        raise HTTPException(status_code=404, detail="商家不存在")
    return {"shop":mock_shops[shop_id], "images": {"data":[]}}

@app.get("/api/shops/{shop_id}/packages")
async def get_shop_packages(shop_id:int):
    """获取商家套餐"""
    return [v for k,v in mock_packages.items()]

@app.get("/api/shops/{shop_id}/reviews")
async def get_shop_reviews(shop_id: int, page: int = 1, limit: int = 10, sort: str = "newest"):
    """获取商家点评"""
    if shop_id not in mock_shops:
        raise HTTPException(status_code=404, detail="商家不存在")
    
    # 简单分页逻辑
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    reviews = mock_reviews.copy()
    if sort == "oldest":
        reviews.reverse()
    
    return {
        "reviews": reviews[start_idx:end_idx],
        "total": len(mock_reviews),
        "page": page,
        "limit": limit,
        "has_more": end_idx < len(mock_reviews)
    }

@app.post("/api/shops/{shop_id}/reviews")
async def create_review(shop_id: int, review_request: ReviewRequest):
    """创建点评"""
    if shop_id not in mock_shops:
        raise HTTPException(status_code=404, detail="商家不存在")
    
    if len(review_request.content.strip()) < 15:
        raise HTTPException(status_code=400, detail="点评内容不能少于15个字符")
    
    # 创建新点评
    new_review = {
        "id": len(mock_reviews) + 1,
        "user_id": mock_user["user_id"],
        "username": mock_user["username"],
        "content": review_request.content,
        "created_at": datetime.now().isoformat() + "Z",
        "replies": []
    }
    
    mock_reviews.insert(0, new_review)  # 新点评插入到最前面
    
    # 模拟奖励券发放逻辑
    user_review_count = len([r for r in mock_reviews if r["user_id"] == mock_user["user_id"]])
    reward_info = None
    if user_review_count >= 3 and user_review_count % 3 == 0:
        reward_info = {
            "coupon_name": "8折优惠券",
            "coupon_value": "最高减20元",
            "expiry_days": 7
        }
    
    return {
        "review": new_review,
        "reward": reward_info,
        "message": "点评发布成功"
    }

@app.post("/api/reviews/{review_id}/replies")
async def create_reply(review_id: int, reply_request: ReplyRequest):
    """回复点评"""
    # 查找目标点评
    target_review = None
    for review in mock_reviews:
        if review["id"] == review_id:
            target_review = review
            break
    
    if not target_review:
        raise HTTPException(status_code=404, detail="点评不存在")
    
    if len(reply_request.content.strip()) < 1:
        raise HTTPException(status_code=400, detail="回复内容不能为空")
    
    # 创建回复
    new_reply = {
        "id": len(target_review["replies"]) + 1,
        "user_id": mock_user["user_id"],
        "username": mock_user["username"],
        "content": reply_request.content,
        "created_at": datetime.now().isoformat() + "Z",
        "parent_id": review_id
    }
    
    target_review["replies"].append(new_reply)
    
    return {
        "reply": new_reply,
        "message": "回复发布成功"
    }

# ==================== 用户相关 API ====================

@app.get("/api/user/reviews")
async def get_user_reviews(page: int = 1, limit: int = 10):
    """获取用户的点评记录"""
    user_reviews = [r for r in mock_reviews if r["user_id"] == mock_user["user_id"]]
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    return {
        "reviews": user_reviews[start_idx:end_idx],
        "total": len(user_reviews),
        "page": page,
        "limit": limit
    }

# ==================== 健康检查 ====================

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# ==================== 静态文件服务 ====================
# 重要：静态文件服务必须在所有API路由之后挂载，否则会拦截API请求

# 静态文件服务 - 将frontend目录挂载到根路径
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# ==================== 启动服务器 ====================

if __name__ == "__main__":
    print("🚀 Starting 小众点评 Mock API Server...")
    print("📱 Frontend: http://127.0.0.1:8000/")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("🔧 Health Check: http://127.0.0.1:8000/api/health")
    
    print(app.routes)
    
    uvicorn.run(
        "mock_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    ) 