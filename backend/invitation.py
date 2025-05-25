from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Dict, Any, List
from backend.database import get_db
from backend.models import User, Order, InvitationRecord
from backend.schema import InvitationRecord as InvitationRecordSchema
from backend.login import get_current_user
from backend.coupons import issue_coupon
from random import choices
from string import ascii_uppercase, digits

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
    return {"code": user.invitation_code, "message": "Success"}

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
    # 检查是否首次下单（确保 is_valid 准确）
    result = await db.execute(
        select(func.count()).where(
            InvitationRecord.invited_user_id == invited_user_id,
            InvitationRecord.is_valid == True
        )
    )
    is_first_invitation = result.scalar() == 0

    record = InvitationRecord(
        inviter_id=inviter_id,
        invited_user_id=invited_user_id,
        order_id=order.id,
        amount=order.order_amount,
        order_time=order.created_at,
        is_valid=is_first_invitation and order.order_amount > 10  # 确保金额条件
    )
    db.add(record)
    await db.commit()

    # 触发奖励
    if record.is_valid:
        await award_invitation_coupon(db, inviter_id)

async def award_invitation_coupon(db: AsyncSession, inviter_id: int):
    try:
        result = await db.execute(
            select(func.count()).where(
                InvitationRecord.inviter_id == inviter_id,
                InvitationRecord.is_valid == True
            )
        )
        invitation_count = result.scalar()
        if invitation_count % 2 == 0:  # 每2次发放
            await issue_coupon(
                db, inviter_id, "invitation", discount_value=20.0, min_spend=0.0
            )
    except Exception as e:
        # 记录日志（此处简化）
        print(f"Failed to award coupon for user {inviter_id}: {str(e)}")