from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from . import models, schema
from .database import get_db
from .login import get_current_user
from .coupons import issue_coupon

router = APIRouter()


@router.post("/shops/{shop_id}/reviews", response_model=schema.ReviewResponse)
async def create_review(
    shop_id: int,
    review: schema.ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    创建点评（需登录）
    """
    # get_current_user 依赖在未认证时会自动抛出 401
    # 校验内容
    if not review.content or not review.content.strip():
        raise HTTPException(status_code=400, detail="点评内容不能为空")

    # 校验商户是否存在
    shop = await db.execute(select(models.Shop).where(models.Shop.id == shop_id))
    shop = shop.scalar()
    if not shop:
        raise HTTPException(status_code=404, detail="商户不存在")

    # 创建并保存点评
    new_review = models.Review(
        user_id=current_user['id'],
        shop_id=shop_id,
        content=review.content.strip(),
        created_at=datetime.utcnow(),
    )

    try:
        db.add(new_review)
        await db.commit()  # 确保事务提交
        await db.refresh(new_review)  # 刷新对象以获取生成的 ID
    except Exception as e:
        await db.rollback()  # 回滚事务以避免数据库锁定
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    
    # 查询用户有效点评数量
    valid_reviews_count = await db.execute(
        select(func.count(models.Review.id)).where(
            models.Review.user_id == current_user['id'],
            func.length(models.Review.content) >= 15
        )
    )
    valid_reviews_count = valid_reviews_count.scalar()

    # 首次达到3条有效点评时发放奖励券
    reward = None
    if valid_reviews_count == 3:
        coupon = await issue_coupon(
            db=db,
            user_id=current_user['id'],
            coupon_type="review",
            discount_value=0.8,  # 8折
            max_discount=20.0,  # 最高抵扣20元
            min_spend=0.0,  # 无门槛
            expiry_days=7  # 7天有效
        )
        reward = schema.ReviewReward(
            coupon_name="点评奖励券",
            coupon_value="8折，最高抵扣20元",
            expiry_days=7
        )
    
    # 显式查询用户的用户名
    user = await db.execute(select(models.User).where(models.User.id == new_review.user_id))
    user = user.scalar()
    username = user.username if user else "未知用户"

    # 返回结果（初始无 replies）
    return {
        "id": new_review.id,
        "user_id": new_review.user_id,
        "username": username,
        "shop_id": new_review.shop_id,
        "content": new_review.content,
        "created_at": new_review.created_at,
        "replies": [],
        "reward": reward
    }


@router.post("/reviews/{review_id}/reply", response_model=schema.ReviewReplyResponse)
async def reply_to_review(
    review_id: int,
    reply: schema.ReviewReplyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    回复点评或回复（支持嵌套，需登录）
    """
    # 校验内容
    if not reply.content or not reply.content.strip():
        raise HTTPException(status_code=400, detail="回复内容不能为空")

    # 校验点评是否存在
    review_obj = await db.execute(select(models.Review).where(models.Review.id == review_id))
    review_obj = review_obj.scalar()
    if not review_obj:
        raise HTTPException(status_code=404, detail="点评不存在")

    # 如指定 parent_reply_id，则校验该回复存在且属于同一点评
    parent_id = reply.parent_reply_id
    if parent_id:
        parent_reply_obj = await db.execute(
            select(models.ReviewReply)
            .where(
                models.ReviewReply.id == parent_id,
                models.ReviewReply.review_id == review_id,
            )
        )
        parent_reply_obj = parent_reply_obj.scalar()
        if not parent_reply_obj:
            raise HTTPException(status_code=404, detail="回复不存在")

    # 创建并保存回复
    new_reply = models.ReviewReply(
        review_id=review_id,
        user_id=current_user['id'],
        content=reply.content.strip(),
        parent_reply_id=parent_id,
        created_at=datetime.utcnow(),
    )

    try:
        db.add(new_reply)
        await db.commit()  # 确保事务提交
        await db.refresh(new_reply)  # 刷新对象以获取生成的 ID
    except Exception as e:
        await db.rollback()  # 回滚事务以避免数据库锁定
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    
    # 显式查询用户的用户名
    user = await db.execute(select(models.User).where(models.User.id == new_reply.user_id))
    user = user.scalar()
    username = user.username if user else "未知用户"


    # 返回结果（初始无子回复）
    return {
        "id": new_reply.id,
        "review_id": new_reply.review_id,
        "user_id": new_reply.user_id,
        "username": username,
        "content": new_reply.content,
        "created_at": new_reply.created_at,
        "parent_reply_id": new_reply.parent_reply_id,
        "replies": [],
    }


@router.get("/shops/{shop_id}/reviews", response_model=list[schema.ReviewResponse])
async def get_shop_reviews(
    shop_id: int,
    page: int = 1,
    limit: int = 10,
    sort: str = "newest",
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取商户全部点评（含嵌套回复，需登录）
    """
    # 校验商户存在
    shop = await db.execute(select(models.Shop).where(models.Shop.id == shop_id))
    shop = shop.scalar()
    if not shop:
        raise HTTPException(status_code=404, detail="商户不存在")
    
    # 排序方式
    order_by_clause = models.Review.created_at.desc() if sort == "newest" else models.Review.created_at.asc()

    # 查询所有点评（按时间倒序）
    reviews = await db.execute(
        select(models.Review)
        .where(models.Review.shop_id == shop_id)
        .order_by(order_by_clause)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    reviews = reviews.scalars().all()

    result = []
    for rv in reviews:
        # 查询该点评的所有回复（按时间正序方便线程展示）
        replies = await db.execute(
            select(models.ReviewReply)
            .where(models.ReviewReply.review_id == rv.id)
            .order_by(models.ReviewReply.created_at.asc())
        )
        replies = replies.scalars().all()

        # 构建 parent_reply_id -> [reply] 映射
        reply_map: dict[int | None, list[models.ReviewReply]] = {}
        for rep in replies:
            reply_map.setdefault(rep.parent_reply_id, []).append(rep)

        # 递归函数：将子回复挂载到父回复
        async def build_node(rep: models.ReviewReply):

            # 显式查询回复用户的用户名
            user = await db.execute(select(models.User).where(models.User.id == rep.user_id))
            user = user.scalar()
            username = user.username if user else "未知用户"

            return {
                "id": rep.id,
                "review_id": rep.review_id,
                "user_id": rep.user_id,
                "content": rep.content,
                "created_at": rep.created_at,
                "parent_reply_id": rep.parent_reply_id,
                "username": username,
                "replies": [await build_node(c) for c in reply_map.get(rep.id, [])],
            }

        # 顶级回复 parent_reply_id 为 None
        root_replies = [await build_node(r) for r in reply_map.get(None, [])]

        # 显式查询点评用户的用户名
        user = await db.execute(select(models.User).where(models.User.id == rv.user_id))
        user = user.scalar()
        username = user.username if user else "未知用户"

        # 组装点评数据
        result.append(
            {
                "id": rv.id,
                "user_id": rv.user_id,
                "shop_id": rv.shop_id,
                "content": rv.content,
                "created_at": rv.created_at,
                "username": username, 
                "replies": root_replies,
            }
        )

    return result

@router.get("/user/reviews", response_model=list[schema.ReviewResponse])
async def get_user_reviews(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    获取用户的点评记录（需登录）
    """
    reviews = await db.execute(
        select(models.Review)
        .where(models.Review.user_id == current_user['id'])
        .order_by(models.Review.created_at.desc())
        .limit(limit)
    )
    reviews = reviews.scalars().all()

    result = []
    for rv in reviews:

        # 显式查询用户的用户名
        user = await db.execute(select(models.User).where(models.User.id == rv.user_id))
        user = user.scalar()
        username = user.username if user else "未知用户"

        result.append(
            {
                "id": rv.id,
                "user_id": rv.user_id,
                "username": username,
                "shop_id": rv.shop_id,
                "content": rv.content,
                "created_at": rv.created_at,
                "replies": [],  # 用户点评记录不需要嵌套回复
            }
        )

    return result