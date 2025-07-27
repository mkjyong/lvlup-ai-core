from __future__ import annotations

from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.deps import get_session
from app.models.game_account import GameAccount
from app.deps import get_current_user

router = APIRouter(prefix="/user", tags=["user"])


class GameIDPatchBody(Dict[str, str]):
    """Dynamic mapping body; validated at runtime."""


@router.get("/game-ids")
async def get_game_ids(user=Depends(get_current_user), session=Depends(get_session)):
    """현재 등록된 게임 계정 ID 목록 반환."""

    result = await session.exec(select(GameAccount).where(GameAccount.user_google_sub == user.google_sub))
    rows = result.all()
    return {row.game: {"account_id": row.account_id, "region": row.region} for row in rows}


@router.patch("/game-ids")
async def patch_game_ids(body: Dict[str, Dict[str, Optional[str]]], user=Depends(get_current_user), session=Depends(get_session)):
    """게임ID / region 업데이트. body 예: {"lol": {"account_id": "Hide on bush", "region": "KR"}}"""

    for game, payload in body.items():
        account_id = payload.get("account_id")
        region = payload.get("region")
        if not account_id:
            raise HTTPException(status_code=400, detail="account_id required")
        result = await session.exec(
            select(GameAccount).where(GameAccount.user_google_sub == user.google_sub, GameAccount.game == game)
        )
        row = result.first()
        if row:
            row.account_id = account_id
            if region:
                row.region = region
        else:
            row = GameAccount(user_google_sub=user.google_sub, game=game, account_id=account_id, region=region)
            session.add(row)
    await session.commit()
    return {"status": "ok"} 