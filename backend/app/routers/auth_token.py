"""JWT Refresh Token Router."""
from fastapi import APIRouter, Cookie, HTTPException, status
from pydantic import BaseModel

from app.services.auth import verify_refresh_token, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class RefreshResponse(BaseModel):
    access_token: str


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token_endpoint(refresh_token: str | None = Cookie(default=None)):
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    try:
        payload = verify_refresh_token(refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    sub = payload.get("sub")
    access_token = create_access_token({"sub": sub})
    return RefreshResponse(access_token=access_token) 