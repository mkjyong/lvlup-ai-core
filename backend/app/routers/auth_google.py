"""Google OAuth 로그인 라우터."""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Query
from pydantic import BaseModel

from app.services import auth_google
from app.services.auth import create_refresh_token, verify_refresh_token, create_access_token
from app.config import get_settings
settings = get_settings()

router = APIRouter(prefix="/auth/google", tags=["auth"])


class TokenRequest(BaseModel):
    id_token: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def google_login(payload: TokenRequest, response: Response, referral_code: str | None = Query(default=None)):
    payload_data = await auth_google.verify_google_id_token(payload.id_token)
    if payload_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    user = await auth_google.get_or_create_user_from_google(payload_data, referral_code=referral_code)

    access_token = create_access_token({"sub": user.google_sub})
    refresh_token = create_refresh_token({"sub": user.google_sub})

    # Secure, HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth/refresh",
    )

    return TokenResponse(access_token=access_token) 