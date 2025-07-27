"""Quota enforcement middleware."""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.usage import has_quota


class QuotaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only apply to /api/coach endpoints
        if request.url.path.startswith("/api/coach"):
            user = request.state.user if hasattr(request.state, "user") else None
            if user:
                ok = await has_quota(user.google_sub, user.plan_tier)
                if not ok:
                    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Monthly quota exceeded")
        response = await call_next(request)
        return response 