from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        query = select(User).where(User.id == user_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        await self._session.refresh(user)
        return user

    async def update_user_profile(
        self,
        user_id: UUID,
        average_cycle_length: Optional[int],
        average_period_length: Optional[int],
        last_period_date: Optional[date],
        is_calculated_default: bool,
    ) -> User | None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(
                average_cycle_length=average_cycle_length,
                average_period_length=average_period_length,
                last_period_date=last_period_date,
                is_calculated_default=is_calculated_default,
            )
            .returning(User)
        )
        try:
            result = await self._session.execute(stmt)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return result.scalar_one_or_none()

    async def update_fields(self, user_id: UUID, values: dict) -> User | None:
        if not values:
            return await self.get_by_id(user_id)

        stmt = update(User).where(User.id == user_id).values(**values).returning(User)
        try:
            result = await self._session.execute(stmt)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        return result.scalar_one_or_none()
