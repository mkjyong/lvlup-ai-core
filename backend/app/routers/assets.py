"""Assets API – 게임 자산 이미지 URL 배치 조회."""

from typing import List

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.services import game_asset as asset_service

router = APIRouter(prefix="/api/assets", tags=["assets"])


class AssetRequest(BaseModel):
    game: str  # lol, pubg
    asset_type: str  # champion, item, weapon
    key: str


class AssetBatchRequest(BaseModel):
    items: List[AssetRequest]


class AssetBatchResponse(BaseModel):
    urls: dict[str, str]  # key 형식: f"{game}:{asset_type}:{key}" -> url


@router.post("/batch", response_model=AssetBatchResponse, status_code=status.HTTP_200_OK)
async def batch_assets(payload: AssetBatchRequest):
    urls: dict[str, str] = {}
    for req in payload.items:
        url = await asset_service.get_asset(req.game, req.asset_type, req.key)
        if url:
            urls[f"{req.game}:{req.asset_type}:{req.key}"] = url
    return AssetBatchResponse(urls=urls) 