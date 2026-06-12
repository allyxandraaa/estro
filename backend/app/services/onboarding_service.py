from datetime import date
from uuid import UUID

from app.repositories.user_repository import UserRepository
from app.schemas.onboarding import OnboardingRequest

DEFAULT_CYCLE_LENGTH = 28
DEFAULT_PERIOD_LENGTH = 5


class OnboardingService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

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

        if data.last_period_date is not None:
            last_period_date = data.last_period_date
        else:
            last_period_date = None
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

        return user
