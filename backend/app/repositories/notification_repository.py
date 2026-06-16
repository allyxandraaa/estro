import uuid
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(
        self,
        user_id: uuid.UUID,
        type_: str,
        scheduled_date: date,
        message: str,
    ) -> None:
        stmt = (
            pg_insert(Notification)
            .values(
                id=uuid.uuid4(),
                user_id=user_id,
                type=type_,
                scheduled_date=scheduled_date,
                message=message,
                is_read=False,
            )
            .on_conflict_do_nothing(
                index_elements=["user_id", "type", "scheduled_date"]
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_all(self, user_id: uuid.UUID, limit: int = 50) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        )
        return result.scalar_one()

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        await self.db.commit()
