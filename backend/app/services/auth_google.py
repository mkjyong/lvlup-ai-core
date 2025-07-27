"""Google OAuth2 인증 서비스."""
from datetime import datetime
from typing import Optional

import google.auth.transport.requests  # type: ignore
from google.oauth2 import id_token  # type: ignore
from sqlmodel import select

from app.config import get_settings
from app.models.user import User
from app.models.db import get_session

settings = get_settings()

CLIENT_ID = settings.GOOGLE_CLIENT_ID if hasattr(settings, "GOOGLE_CLIENT_ID") else ""


async def verify_google_id_token(token: str) -> dict | None:  # noqa: D401
    """ID Token 검증 후 페이로드 반환."""
    try:
        # google-auth verify (sync) – wrap in executor to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        payload = await loop.run_in_executor(
            None,
            id_token.verify_oauth2_token,
            token,
            google.auth.transport.requests.Request(),
            CLIENT_ID,
        )
        return payload
    except Exception:
        return None


async def get_or_create_user_from_google(payload: dict, referral_code: str | None = None) -> User:
    google_sub = payload["sub"]
    email = payload.get("email")
    picture = payload.get("picture")

    async with get_session() as session:
        result = await session.exec(select(User).where(User.google_sub == google_sub))  # type: ignore[attr-defined]
        user: Optional[User] = result.one_or_none()

        is_new = user is None

        # 신규 가입자 – 사용자 데이터 및 레퍼럴 코드 생성
        if is_new:
            from app.services.referral import generate_unique_referral_code

            # 고유 레퍼럴 코드 확보
            new_code = await generate_unique_referral_code(session)

            user = User(
                google_sub=google_sub,  # type: ignore[arg-type]
                email=email,
                avatar=picture,
                plan_tier="free",
                referral_code=new_code,
                referral_credits=0,
                created_at=datetime.utcnow(),
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            # 추천 코드가 제공된 경우, 추천 포인트 적립
            if referral_code:
                from app.models.referral import Referral

                # 본인 코드 사용 방지 & 유효 코드 확인
                referrer_result = await session.exec(
                    select(User).where(User.referral_code == referral_code)  # type: ignore[attr-defined]
                )
                referrer: Optional[User] = referrer_result.one_or_none()

                if referrer and referrer.google_sub != user.google_sub:
                    # 이미 동일 referrer/referred 조합이 있는지 확인(중복 방지)
                    dup_q = await session.exec(
                        select(Referral).where(
                            (Referral.referrer_google_sub == referrer.google_sub)
                            & (Referral.referred_google_sub == user.google_sub)
                        )
                    )
                    if dup_q.one_or_none() is None:
                        referral = Referral(
                            referrer_google_sub=referrer.google_sub,
                            referred_google_sub=user.google_sub,
                        )
                        session.add(referral)

                        await session.commit()

        return user 