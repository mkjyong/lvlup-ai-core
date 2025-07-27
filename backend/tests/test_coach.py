import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ask_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/api/coach/ask", json={"question": "Hello?"})
        assert resp.status_code == 200
        assert "answer" in resp.json() 