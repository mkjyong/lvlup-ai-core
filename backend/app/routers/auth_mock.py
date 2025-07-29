from __future__ import annotations

import os
from fastapi import APIRouter, status
from pydantic import BaseModel
from app.services.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"], include_in_schema=False)


class _Creds(BaseModel):
    email: str
    password: str


class _TokenRes(BaseModel):
    access_token: str


@router.post("/signup", response_model=_TokenRes, status_code=status.HTTP_201_CREATED)
async def signup(creds: _Creds):
    token = create_access_token({"sub": creds.email})
    return _TokenRes(access_token=token)


@router.post("/login", response_model=_TokenRes)
async def login(creds: _Creds):
    token = create_access_token({"sub": creds.email})
    return _TokenRes(access_token=token) 