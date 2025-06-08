from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Dict, Any, List
from backend.database import get_db
from backend.models import User, Order, InvitationRecord
from backend.models import InvitationRecord as InvitationRecordSchema, UserCoupon, Coupon
from backend.schema import InvitationCodeRequest, RewardCoupon
from backend.login import get_current_user
from backend.coupons import issue_coupon
from random import choices
from string import ascii_uppercase, digits
from datetime import timedelta

router = APIRouter()

async def generate_invitation_code(db: AsyncSession, user_id: int) -> str:
    for _ in range(10):  # 最多尝试10次
        code = ''.join(choices(ascii_uppercase + digits, k=6))
        try:
            user = await db.get(User, user_id)
            user.invitation_code = code
            await db.commit()
            return code
        except Exception as e:
            if "unique constraint" in str(e).lower():
                continue  # 冲突，重试
            raise HTTPException(status_code=500, detail="生成邀请码失败")
    raise HTTPException(status_code=500, detail="无法生成唯一邀请码")

@router.get("/invitation/code", response_model=Dict[str, str])
async def get_invitation_code(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if not user.invitation_code:
        user.invitation_code = await generate_invitation_code(db, user_id)
        await db.commit()
    return {"code": user.invitation_code}

@router.get("/invitation/records", response_model=Dict[str, Any])
async def get_invitation_records(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    result = await db.execute(
        select(InvitationRecord, User)
        .join(User, InvitationRecord.invited_user_id == User.id)
        .where(InvitationRecord.inviter_id == user_id)
    )
    records = result.all()
    return {
        "records": [
            {
                "user_id": r.InvitationRecord.invited_user_id,
                "username": r.User.username,
                "order_time": r.InvitationRecord.order_time,
                "amount": r.InvitationRecord.amount
            } for r in records
        ],
        "total_invited": len(records)
    }

async def record_invitation(db: AsyncSession, order: Order, inviter_id: int, invited_user_id: int):
    # 检查订单金额是否满足条件
    if order.order_amount <= 10:
        return
    
    # 检查是否已有有效邀请记录
    existing_record = await db.execute(
        select(InvitationRecord).where(
            InvitationRecord.invited_user_id == invited_user_id,
            InvitationRecord.is_valid == True
        )
    )
    if existing_record.scalar():
        return
        
    # 创建新记录
    record = InvitationRecord(
        inviter_id=inviter_id,
        invited_user_id=invited_user_id,
        order_id=order.id,
        amount=order.order_amount,
        order_time=order.created_at,
        is_valid=True
    )
    db.add(record)
    await db.commit()
    
    # 触发奖励
    await award_invitation_coupon(db, inviter_id)

async def award_invitation_coupon(db: AsyncSession, inviter_id: int):
    try:
        # 查询用户的有效邀请记录数
        result = await db.execute(
            select(func.count()).where(
                InvitationRecord.inviter_id == inviter_id,
                InvitationRecord.is_valid == True
            )
        )
        invitation_count = result.scalar()
        print(f"用户 {inviter_id} 的有效邀请记录数：{invitation_count}")

        # 查询用户已领取的邀请奖励券数量
        result = await db.execute(
            select(func.count(UserCoupon.id)).join(Coupon, UserCoupon.coupon_id == Coupon.id).where(
                UserCoupon.user_id == inviter_id,
                Coupon.category == "invitation"
            )
        )
        issued_coupons_count = result.scalar() or 0
        print(f"用户 {inviter_id} 已领取的邀请奖励券数量：{issued_coupons_count}")

        # 计算应发放的奖励券数量
        eligible_coupons_count = invitation_count // 2
        if eligible_coupons_count > issued_coupons_count:
            # 发放新的奖励券
            for _ in range(eligible_coupons_count - issued_coupons_count):
                print(f"正在发放邀请奖励券给用户 {inviter_id}")
                await issue_coupon(
                    db, inviter_id, "invitation", discount_value=20.0, min_spend=0.0, expiry_days=7
                )

    except Exception as e:
        # 记录日志
        print(f"Failed to award coupon for user {inviter_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="奖励券发放失败")

@router.get("/invitation/rewards", response_model=List[RewardCoupon])
async def get_invitation_rewards(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        # 检查是否需要创建奖励券
        inviter_id = current_user["id"]
        result = await db.execute(
            select(func.count()).where(
                InvitationRecord.inviter_id == inviter_id,
                InvitationRecord.is_valid == True
            )
        )
        invitation_count = result.scalar()
        print(f"User {inviter_id} has {invitation_count} valid invitations.")

        # 如果满足条件但奖励券尚未创建，触发奖励券创建逻辑
        if invitation_count > 0 and invitation_count % 2 == 0:
            await award_invitation_coupon(db, inviter_id)

        # 查询奖励券
        result = await db.execute(
            select(UserCoupon, Coupon)
            .join(Coupon, UserCoupon.coupon_id == Coupon.id)
            .where(
                UserCoupon.user_id == current_user["id"],
                Coupon.category == "invitation"
            )
            .order_by(UserCoupon.claimed_at.desc())
        )
        rewards = result.all()
        print(f"Fetched reward coupons for user {current_user['id']}: {rewards}")

        print("Serialized reward coupons:", [
            {
                "id": uc.id,
                "name": c.name,
                "value": c.discount_value,
                "type": c.discount_type.value,
                "description": c.description,
                "issued_date": uc.claimed_at.isoformat() if uc.claimed_at else None,
                "expiry_date": uc.expires_at.isoformat() if uc.expires_at else None,
                "status": uc.status.value
            }
            for uc, c in rewards
        ])
        
        # 序列化返回数据
        return [
            RewardCoupon(
                id=uc.id,
                name=c.name,
                value=c.discount_value,
                type=c.discount_type.value,
                description=c.description,
                issued_date=uc.claimed_at,
                expiry_date=uc.expires_at,
                status=uc.status.value
            )
            for uc, c in rewards
        ]
    except Exception as e:
        print(f"Failed to fetch reward coupons: {str(e)}")  # 添加日志
        raise HTTPException(status_code=500, detail="获取奖励券失败")

@router.post("/invitation/validate", response_model=Dict[str, Any])
async def validate_invitation_code(
    request: InvitationCodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    code = request.code

    # 检查邀请码是否存在
    result = await db.execute(select(User).where(User.invitation_code == code))
    inviter = result.scalar()
    if not inviter:
        raise HTTPException(status_code=400, detail="邀请码不存在或已失效")
    
    # 检查是否是自己的邀请码
    if inviter.id == current_user["id"]:
        raise HTTPException(status_code=400, detail="不能使用自己的邀请码")
    
    # 检查是否已使用过邀请码
    result = await db.execute(
        select(InvitationRecord).where(
            InvitationRecord.invited_user_id == current_user["id"],
            InvitationRecord.is_valid == True
        )
    )
    if result.scalar():
        raise HTTPException(status_code=400, detail="您已使用过邀请码，每个用户只能使用一次")
    
    return {"message": "邀请码验证成功"}