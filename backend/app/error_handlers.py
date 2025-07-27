"""글로벌 예외 핸들러 등록 헬퍼."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import AIError


def register_exception_handlers(app: FastAPI) -> None:  # noqa: D401
    """예외 핸들러 등록."""

    @app.exception_handler(AIError)
    async def _ai_error_handler(_request: Request, exc: AIError):  # noqa: D401
        return JSONResponse(status_code=exc.status_code, content=exc.to_dict()) 

    @app.exception_handler(Exception)
    async def _general_exception_handler(request: Request, exc: Exception):  # noqa: D401
        import traceback
        from app.services import slack as _slack

        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[:18000]
        await _slack.notify_backend_error(tb)
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"}) 