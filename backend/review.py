from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from . import models, schema
from .database import get_db
from .utils import get_current_user

router = APIRouter()


@router.post("/shops/{shop_id}/reviews", response_model=schema.ReviewResponse)
def create_review(
    shop_id: int,
    review: schema.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    创建点评（需登录）
    """
    # get_current_user 依赖在未认证时会自动抛出 401
    # 校验内容
    if not review.content or not review.content.strip():
        raise HTTPException(status_code=400, detail="点评内容不能为空")

    # 校验商户是否存在
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="商户不存在")

    # 创建并保存点评
    new_review = models.Review(
        user_id=current_user.id,
        shop_id=shop_id,
        content=review.content.strip(),
        created_at=datetime.utcnow(),
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)

    # 返回结果（初始无 replies）
    return {
        "id": new_review.id,
        "user_id": new_review.user_id,
        "shop_id": new_review.shop_id,
        "content": new_review.content,
        "created_at": new_review.created_at,
        "replies": [],
    }


@router.post("/reviews/{review_id}/reply", response_model=schema.ReviewReplyResponse)
def reply_to_review(
    review_id: int,
    reply: schema.ReviewReplyCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    回复点评或回复（支持嵌套，需登录）
    """
    # 校验内容
    if not reply.content or not reply.content.strip():
        raise HTTPException(status_code=400, detail="回复内容不能为空")

    # 校验点评是否存在
    review_obj = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review_obj:
        raise HTTPException(status_code=404, detail="点评不存在")

    # 如指定 parent_reply_id，则校验该回复存在且属于同一点评
    parent_id = reply.parent_reply_id
    if parent_id:
        parent_reply_obj = (
            db.query(models.ReviewReply)
            .filter(
                models.ReviewReply.id == parent_id,
                models.ReviewReply.review_id == review_id,
            )
            .first()
        )
        if not parent_reply_obj:
            raise HTTPException(status_code=404, detail="回复不存在")

    # 创建并保存回复
    new_reply = models.ReviewReply(
        review_id=review_id,
        user_id=current_user.id,
        content=reply.content.strip(),
        parent_reply_id=parent_id,
        created_at=datetime.utcnow(),
    )
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)

    # 返回结果（初始无子回复）
    return {
        "id": new_reply.id,
        "review_id": new_reply.review_id,
        "user_id": new_reply.user_id,
        "content": new_reply.content,
        "created_at": new_reply.created_at,
        "parent_reply_id": new_reply.parent_reply_id,
        "replies": [],
    }


@router.get("/shops/{shop_id}/reviews", response_model=list[schema.ReviewResponse])
def get_shop_reviews(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    获取商户全部点评（含嵌套回复，需登录）
    """
    # 校验商户存在
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="商户不存在")

    # 查询所有点评（按时间倒序）
    reviews = (
        db.query(models.Review)
        .filter(models.Review.shop_id == shop_id)
        .order_by(models.Review.created_at.desc())
        .all()
    )

    result = []
    for rv in reviews:
        # 查询该点评的所有回复（按时间正序方便线程展示）
        replies = (
            db.query(models.ReviewReply)
            .filter(models.ReviewReply.review_id == rv.id)
            .order_by(models.ReviewReply.created_at.asc())
            .all()
        )

        # 构建 parent_reply_id -> [reply] 映射
        reply_map: dict[int | None, list[models.ReviewReply]] = {}
        for rep in replies:
            reply_map.setdefault(rep.parent_reply_id, []).append(rep)

        # 递归函数：将子回复挂载到父回复
        def build_node(rep: models.ReviewReply):
            return {
                "id": rep.id,
                "review_id": rep.review_id,
                "user_id": rep.user_id,
                "content": rep.content,
                "created_at": rep.created_at,
                "parent_reply_id": rep.parent_reply_id,
                "replies": [build_node(c) for c in reply_map.get(rep.id, [])],
            }

        # 顶级回复 parent_reply_id 为 None
        root_replies = [build_node(r) for r in reply_map.get(None, [])]

        # 组装点评数据
        result.append(
            {
                "id": rv.id,
                "user_id": rv.user_id,
                "shop_id": rv.shop_id,
                "content": rv.content,
                "created_at": rv.created_at,
                "replies": root_replies,
            }
        )

    return result
