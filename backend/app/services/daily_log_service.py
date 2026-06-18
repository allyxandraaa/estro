import uuid
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_log import DailyLog
from app.repositories.daily_log_repository import DailyLogRepository

MAX_RANGE_DAYS = 366


class DailyLogService:
    def __init__(self, db: AsyncSession):
        self.repository = DailyLogRepository(db)

    async def upsert(self, user_id: uuid.UUID, log_date: date, **fields) -> DailyLog:
        return await self.repository.upsert(user_id, log_date, **fields)

    async def get_by_date(self, user_id: uuid.UUID, log_date: date) -> DailyLog | None:
        return await self.repository.get_by_date(user_id, log_date)

    async def get_range(
        self, user_id: uuid.UUID, date_from: date, date_to: date
    ) -> list[DailyLog]:
        if date_to < date_from:
            raise ValueError("date_to не може бути раніше date_from")

        if (date_to - date_from).days + 1 > MAX_RANGE_DAYS:
            raise ValueError(f"Максимальний діапазон — {MAX_RANGE_DAYS} днів")

        return await self.repository.get_range(user_id, date_from, date_to)

    async def delete(self, user_id: uuid.UUID, log_date: date) -> bool:
        return await self.repository.delete(user_id, log_date)