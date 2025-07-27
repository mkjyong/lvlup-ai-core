from __future__ import annotations

"""Referral 관련 API 라우터."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.deps import get_current_user
from app.models.db import get_session
from app.models.user import User
from app.models.referral import Referral
from app.services.referral import generate_unique_referral_code

router = APIRouter(prefix="/referral", tags=["referral"])


class ReferralInfo(BaseModel):
    referral_code: str | None
    credits: int
    referred_count: int


@router.get("/me", response_model=ReferralInfo)
async def get_my_referral_info(current_user: User = Depends(get_current_user)):
    """현재 로그인한 사용자의 레퍼럴 현황을 조회한다."""

    async with get_session() as session:
        # 추천해온 사용자 수 계산
        result = await session.exec(
            select(Referral).where(Referral.referrer_google_sub == current_user.google_sub)
        )
        referred_count = len(result.all())

    return ReferralInfo(
        referral_code=current_user.referral_code,
        credits=current_user.referral_credits,
        referred_count=referred_count,
    )

# ------------------------------------------------------------------
# New – Issue referral code
# ------------------------------------------------------------------


@router.post("/issue", response_model=ReferralInfo)
async def issue_referral_code(current_user: User = Depends(get_current_user)):
    """사용자에게 신규 레퍼럴 코드를 발급한다.

    이미 코드가 존재하면 400 에러를 반환한다.
    """

    if current_user.referral_code:
        raise HTTPException(status_code=400, detail="referral code already issued")

    async with get_session() as session:
        # 고유 코드 생성 및 저장
        new_code = await generate_unique_referral_code(session)

        stmt = select(User).where(User.google_sub == current_user.google_sub).limit(1)
        result = await session.exec(stmt)
        user: User = result.one()
        user.referral_code = new_code

        await session.commit()

        # 추천인 수 0, 크레딧 0 으로 초기화
        referred_count = 0

    return ReferralInfo(referral_code=new_code, credits=user.referral_credits, referred_count=referred_count) 