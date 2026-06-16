from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.onboarding_controller import get_current_user_id
from app.database import get_session
from app.repositories.user_repository import UserRepository
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.utils.profile import derive_name_from_email

router = APIRouter(prefix="/api/users", tags=["Profile"])


def _get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    repository: UserRepository = Depends(_get_user_repository),
) -> ProfileResponse:
    user = await repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача для цього токена не знайдено",
        )

    if not user.name:
        updated = await repository.update_fields(
            user_id,
            {"name": derive_name_from_email(user.email)},
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Користувача для цього токена не знайдено",
            )
        user = updated

    return ProfileResponse.model_validate(user)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    repository: UserRepository = Depends(_get_user_repository),
) -> ProfileResponse:
    user = await repository.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача для цього токена не знайдено",
        )

    values = data.model_dump(exclude_unset=True)
    if "name" in values and values["name"] is not None:
        values["name"] = values["name"].strip()
    if "email" in values and values["email"] is not None:
        values["email"] = str(values["email"])
        existing = await repository.get_by_email(values["email"])
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already in use",
            )
        if not values.get("name") and not user.name:
            values["name"] = derive_name_from_email(values["email"])

    next_cycle_length = values.get("average_cycle_length", user.average_cycle_length)
    next_period_length = values.get("average_period_length", user.average_period_length)
    if (
        next_cycle_length is not None
        and next_period_length is not None
        and next_period_length >= next_cycle_length
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Тривалість менструації має бути меншою за тривалість циклу",
        )

    try:
        updated_user = await repository.update_fields(user_id, values)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already in use",
        ) from None

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача для цього токена не знайдено",
        )

    return ProfileResponse.model_validate(updated_user)
