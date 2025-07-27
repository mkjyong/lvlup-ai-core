from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="헬스 체크", response_model=dict)
async def healthcheck() -> dict[str, str]:
    """애플리케이션 헬스 체크 엔드포인트.

    Returns
    -------
    dict[str, str]
        상태 정보 (고정)
    """
    return {"status": "ok"} 