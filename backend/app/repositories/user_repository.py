from uuid import UUID

from sqlalchemy import select
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

    async def update_onboarding(self, user_id: UUID, cycle_length: int, period_length: int) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.average_cycle_length = cycle_length
        user.average_period_length = period_length
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        await self._session.refresh(user)
        return user
