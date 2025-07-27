"""Request ID Middleware.

Generates a UUID4 request ID for every incoming HTTP request, binds it to
structlog contextvars and exposes it via `X-Request-ID` response header.
"""
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # Bind to structlog contextvars
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            # Clear to avoid leaking.
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-ID"] = request_id
        return response 