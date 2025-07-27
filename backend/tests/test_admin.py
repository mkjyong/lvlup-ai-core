import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_stats_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.get("/admin/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "cost" in data
        assert "cache_hit_rate" in data 