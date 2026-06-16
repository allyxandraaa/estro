import uuid
from datetime import date
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_log import DailyLog


_PROTECTED_KEYS = frozenset({"user_id", "date", "id"})


class DailyLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, user_id: uuid.UUID, log_date: date, **fields: Any) -> DailyLog | None:
        mutable = {k: v for k, v in fields.items() if k not in _PROTECTED_KEYS}
        if not mutable:
            return await self.get_by_date(user_id, log_date)

        values = {
            "user_id": user_id,
            "date": log_date,
            **mutable,
        }

        stmt = (
            insert(DailyLog)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["user_id", "date"],
                set_=mutable,
            )
            .returning(DailyLog)
        )

        await self.db.execute(stmt)
        await self.db.commit()
        return await self.get_by_date(user_id, log_date)

    async def get_by_date(self, user_id: uuid.UUID, log_date: date) -> DailyLog | None:
        result = await self.db.execute(
            select(DailyLog).where(
                DailyLog.user_id == user_id,
                DailyLog.date == log_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_range(
        self, user_id: uuid.UUID, date_from: date, date_to: date
    ) -> list[DailyLog]:
        result = await self.db.execute(
            select(DailyLog)
            .where(
                DailyLog.user_id == user_id,
                DailyLog.date >= date_from,
                DailyLog.date <= date_to,
            )
            .order_by(DailyLog.date.asc())
        )
        return list(result.scalars().all())

    async def delete(self, user_id: uuid.UUID, log_date: date) -> bool:
        result = await self.db.execute(
            delete(DailyLog).where(
                DailyLog.user_id == user_id,
                DailyLog.date == log_date,
            )
        )
        await self.db.commit()
        return result.rowcount > 0