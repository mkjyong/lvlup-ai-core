from fastapi import FastAPI

from app.logging import init_logging
from prometheus_fastapi_instrumentator import Instrumentator
from app.error_handlers import register_exception_handlers
from app.routers import health
from app.routers import auth_google as google_router
from app.routers import auth_token as token_router
from app.routers import coach as coach_router
from app.routers import admin as admin_router
from app.routers import billing as billing_router
from app.routers import referral as referral_router
from app.routers import user as user_router
from app.routers import performance as performance_router
from app.routers import assets as assets_router
from app.models.db import init_db
from app.config import get_settings
from app.middleware.quota import QuotaMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.geoip import GeoIPMiddleware
from app.deps import get_current_user
from fastapi import Request, HTTPException, status



def create_app() -> FastAPI:
    """FastAPI 앱 팩토리.

    모든 라우터, 미들웨어, 이벤트 훅을 등록한다.
    """

    # 로깅 초기화는 가장 먼저 수행
    init_logging()

    app = FastAPI(title="AI Coach Backend", version="0.1.0")

    # 미들웨어: quota
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(GeoIPMiddleware)
    app.add_middleware(QuotaMiddleware)

    # CORS – 허용 Origin 을 환경변수 `CORS_ALLOW_ORIGINS`(쉼표 구분) 로 관리
    from fastapi.middleware.cors import CORSMiddleware

    cors_origins = []
    raw_origins = get_settings().dict().get("CORS_ALLOW_ORIGINS")  # type: ignore[arg-type]
    if raw_origins:
        cors_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.middleware("http")
    async def add_user_to_state(request: Request, call_next):
        # attach user if Authorization header present
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            try:
                user = await get_current_user(auth)
                request.state.user = user
            except HTTPException:
                pass
        return await call_next(request)

    # Router 등록
    app.include_router(health.router)
    app.include_router(google_router.router)
    app.include_router(coach_router.router)
    app.include_router(token_router.router)
    app.include_router(admin_router.router)
    app.include_router(billing_router.router)
    app.include_router(referral_router.router)
    app.include_router(user_router.router)
    app.include_router(performance_router.router)
    app.include_router(assets_router.router)

    # 예외 핸들러 등록
    register_exception_handlers(app)

    # Prometheus metrics
    if get_settings().PROMETHEUS_ENABLED:
        Instrumentator().instrument(app).expose(app)

    # 이벤트 훅: DB 초기화
    @app.on_event("startup")
    async def _startup_event():  # noqa: D401
        """애플리케이션 시작 시 초기화 작업."""

        if get_settings().AUTO_MIGRATE:
            await init_db()

    @app.on_event("shutdown")
    async def _shutdown_event():  # noqa: D401
        """종료 시 외부 클라이언트 정리."""

        # RevenueCat HTTPX 클라이언트 종료
        from app.services import revenuecat as _rc

        if hasattr(_rc, "_client") and not _rc._client.is_closed:  # type: ignore[attr-defined]
            import asyncio

            # ensure awaitable in shutdown
            if asyncio.iscoroutinefunction(_rc._client.aclose):
                await _rc._client.aclose()

    return app


app = create_app()  # ASGI 애플리케이션 인스턴스 