import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.cycle_repository import CycleRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository

from app.services.cycle_projection_service import CycleProjectionService

_MONTHS_GEN = [
    "січня", "лютого", "березня", "квітня", "травня", "червня",
    "липня", "серпня", "вересня", "жовтня", "листопада", "грудня",
]

WINDOW_DAYS = 3


def _fmt(d: date) -> str:
    return f"{d.day} {_MONTHS_GEN[d.month - 1]}"


class NotificationService:
    def __init__(self, db: AsyncSession):
        self._notif = NotificationRepository(db)
        self._proj = CycleProjectionService(
            user_repository=UserRepository(db),
            cycle_repository=CycleRepository(db),
        )

    async def get_and_generate(self, user_id: uuid.UUID) -> dict:
        await self._generate(user_id)
        notifications = await self._notif.get_all(user_id)
        unread = await self._notif.get_unread_count(user_id)
        return {
            "notifications": [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "scheduled_date": n.scheduled_date,
                    "message": n.message,
                    "is_read": n.is_read,
                    "created_at": n.created_at,
                }
                for n in notifications
            ],
            "unread_count": unread,
        }

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self._notif.mark_all_read(user_id)

    async def _generate(self, user_id: uuid.UUID) -> None:
        today = date.today()
        until = today + timedelta(days=WINDOW_DAYS + 1)

        active_cycle = await self._proj.cycle_repository.get_active_cycle(user_id)
        projections = await self._proj.calculate_cycle_projections(
            user_id,
            until,
            active_start=active_cycle.start_date if active_cycle else None,
        )

        for proj in projections:
            # Менструація: якщо старт прогнозу в межах 1..WINDOW_DAYS днів
            days_to_men = (proj.predicted_start_date - today).days
            if 1 <= days_to_men <= WINDOW_DAYS:
                await self._notif.upsert(
                    user_id=user_id,
                    type_="menstruation_soon",
                    scheduled_date=proj.predicted_start_date,
                    message=f"Менструація очікується {_fmt(proj.predicted_start_date)}",
                )

            # Овуляція: якщо дата ov у межах 1..WINDOW_DAYS днів
            days_to_ov = (proj.predicted_ovulation_date - today).days
            if 1 <= days_to_ov <= WINDOW_DAYS:
                await self._notif.upsert(
                    user_id=user_id,
                    type_="ovulation_soon",
                    scheduled_date=proj.predicted_ovulation_date,
                    message=f"Овуляція очікується {_fmt(proj.predicted_ovulation_date)}",
                )
