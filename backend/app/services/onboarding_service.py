from uuid import UUID

from app.repositories.user_repository import UserRepository
from app.schemas.onboarding import OnboardingRequest

DEFAULT_CYCLE_LENGTH = 28
DEFAULT_PERIOD_LENGTH = 5


class OnboardingService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def save_onboarding(self, user_id: UUID, data: OnboardingRequest):
        cycle_length = data.cycle_length if data.cycle_length is not None else DEFAULT_CYCLE_LENGTH
        period_length = data.period_length if data.period_length is not None else DEFAULT_PERIOD_LENGTH

        user = await self._repository.update_onboarding(
            user_id=user_id,
            cycle_length=cycle_length,
            period_length=period_length,
        )

        if not user:
            raise ValueError("User not found")

        return user
