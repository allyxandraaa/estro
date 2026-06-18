from datetime import date, timedelta
from uuid import UUID

from app.repositories.cycle_repository import CycleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.onboarding import OnboardingRequest

DEFAULT_CYCLE_LENGTH = 28
DEFAULT_PERIOD_LENGTH = 5


class OnboardingService:
    def __init__(self, repository: UserRepository, cycle_repository: CycleRepository):
        self._repository = repository
        self._cycle_repository = cycle_repository

    async def save_onboarding(self, user_id: UUID, data: OnboardingRequest):
        is_calculated = False

        if data.cycle_length is not None:
            cycle_length = data.cycle_length
        else:
            cycle_length = DEFAULT_CYCLE_LENGTH
            is_calculated = True

        if data.period_length is not None:
            period_length = data.period_length
        else:
            period_length = DEFAULT_PERIOD_LENGTH
            is_calculated = True

        last_period_date = data.last_period_date
        if last_period_date is None:
            is_calculated = True

        user = await self._repository.update_user_profile(
            user_id=user_id,
            average_cycle_length=cycle_length,
            average_period_length=period_length,
            last_period_date=last_period_date,
            is_calculated_default=is_calculated,
        )

        if not user:
            raise ValueError("User not found")

        # Створюємо початковий цикл тільки якщо юзер явно вказав дату останньої менструації.
        # Якщо пропустив — нічого не створюємо, юзер відмітить сам.
        if last_period_date is not None:
            has_active = await self._cycle_repository.get_active_cycle(user_id)
            has_completed = await self._cycle_repository.get_last_completed_cycles(user_id, limit=1)
            if not has_active and not has_completed:
                cycle = await self._cycle_repository.create_cycle(user_id, last_period_date)
                expected_end = last_period_date + timedelta(days=period_length - 1)
                if expected_end < date.today():
                    await self._cycle_repository.close_cycle(cycle, expected_end)

        return user
