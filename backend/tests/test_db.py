import pytest

from app.models.db import get_session


@pytest.mark.asyncio
async def test_get_session_yields():
    # dependency generator test
    async with get_session() as session:
        assert session is not None 