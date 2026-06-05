from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.repositories.user_repository import UserRepository
from app.schemas.onboarding import OnboardingRequest
from app.services.onboarding_service import OnboardingService

router = APIRouter(prefix="/api/users", tags=["Onboarding"])

bearer_scheme = HTTPBearer()


def _get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UUID:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалідний токен",
            )
        return UUID(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалідний токен",
        )


def _get_onboarding_service(
    session: AsyncSession = Depends(get_session),
) -> OnboardingService:
    repository = UserRepository(session)
    return OnboardingService(repository)


@router.post("/onboarding", status_code=status.HTTP_200_OK)
async def onboarding(
    data: OnboardingRequest,
    user_id: UUID = Depends(_get_current_user_id),
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
