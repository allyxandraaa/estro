import uuid
from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.cycle_repository import CycleRepository


class CycleService:
    def __init__(self, db: AsyncSession):
        self.repository = CycleRepository(db)

    async def start_cycle(self, user_id: uuid.UUID, start_date: date):
        if start_date > date.today():
            raise ValueError("Дата не може бути в майбутньому")

        active = await self.repository.get_active_cycle(user_id)
        if active:
            raise ValueError("Вже є відкритий цикл")

        try:
            return await self.repository.create_cycle(user_id, start_date)
        except IntegrityError:
            raise ValueError("Вже є відкритий цикл") from None

    async def end_cycle(self, user_id: uuid.UUID, end_date: date):
        if end_date > date.today():
            raise ValueError("Дата не може бути в майбутньому")

        active = await self.repository.get_active_cycle(user_id)
        if not active:
            raise ValueError("Немає відкритого циклу")

        if end_date < active.start_date:
            raise ValueError("Дата закінчення не може бути раніше дати початку")

        try:
            return await self.repository.close_cycle(active, end_date)
        except IntegrityError as e:
            raise ValueError("Помилка збереження циклу") from e
