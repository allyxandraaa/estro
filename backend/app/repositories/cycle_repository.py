import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cycle import Cycle


class CycleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_cycle(self, user_id: uuid.UUID) -> Cycle | None:
        result = await self.db.execute(
            select(Cycle)
            .where(Cycle.user_id == user_id, Cycle.end_date.is_(None))
        )
        return result.scalar_one_or_none()

    async def create_cycle(self, user_id: uuid.UUID, start_date: date) -> Cycle:
        cycle = Cycle(user_id=user_id, start_date=start_date)
        self.db.add(cycle)
        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    async def close_cycle(self, cycle: Cycle, end_date: date) -> Cycle:
        cycle.end_date = end_date
        await self.db.commit()
        await self.db.refresh(cycle)
        return cycle

    async def get_last_completed_cycles(self, user_id: uuid.UUID, limit: int = 10) -> list[Cycle]:
        result = await self.db.execute(
            select(Cycle)
            .where(Cycle.user_id == user_id, Cycle.end_date.is_not(None))
            .order_by(Cycle.start_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
