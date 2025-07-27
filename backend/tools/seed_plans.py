"""Seed initial PlanTier rows (FREE, BASIC, BASIC_ANNUAL)."""
import asyncio

from app.models.db import get_session
from app.models.plan_tier import PlanTier


async def _seed() -> None:
    async with get_session() as session:
        # check existing
        existing = await session.exec(PlanTier.select())  # type: ignore[attr-defined]
        if existing.first():
            print("PlanTier rows already exist; skipping seed.")
            return
        free = PlanTier(
            name="free",
            price_usd=0.0,
            prompt_limit=500,
            completion_limit=1000,
            weekly_request_limit=30,
            monthly_request_limit=200,
        )
        basic = PlanTier(
            name="basic",
            price_usd=10.0,
            prompt_limit=1000,
            completion_limit=2000,
            weekly_request_limit=200,
            monthly_request_limit=800,
            special_monthly_request_limit=100,
        )
        basic_annual = PlanTier(
            name="basic_annual",
            price_usd=100.0,
            prompt_limit=1000,
            completion_limit=2000,
            weekly_request_limit=200,
            monthly_request_limit=800,
            special_monthly_request_limit=100,
        )
        session.add_all([free, basic, basic_annual])
        await session.commit()
        print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(_seed()) 