from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user_id
from app.repositories.user_repository import UserRepository
from app.schemas.onboarding import OnboardingRequest
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/api/users", tags=["Onboarding"])


def _get_onboarding_service(
    session: AsyncSession = Depends(get_session),
) -> OnboardingService:
    repository = UserRepository(session)
    return OnboardingService(repository)


@router.post("/onboarding", status_code=status.HTTP_200_OK)
async def onboarding(
    data: OnboardingRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: OnboardingService = Depends(_get_onboarding_service),
):
    try:
        await service.save_onboarding(user_id=user_id, data=data)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Користувача не знайдено",
        )
    return {"message": "Онбординг завершено успішно"}
