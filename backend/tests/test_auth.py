import uuid

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_signup_and_login():
    email = f"user-{uuid.uuid4()}@example.com"
    password = "password123"

    async with AsyncClient(app=app, base_url="http://test") as ac:
        # signup
        resp = await ac.post("/auth/signup", json={"email": email, "password": password})
        assert resp.status_code == 201
        access_token = resp.json()["access_token"]
        assert access_token

        # login
        resp2 = await ac.post("/auth/login", json={"email": email, "password": password})
        assert resp2.status_code == 200
        assert resp2.json()["access_token"] 