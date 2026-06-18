from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.onboarding_controller import get_current_user_id
from app.database import get_session
from app.repositories.cycle_repository import CycleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.cycle_projection_service import CycleProjectionService
from app.utils.profile import derive_name_from_email

router = APIRouter(prefix="/api/users", tags=["Profile"])


async def _profile_response(user, session: AsyncSession) -> ProfileResponse:
    cycle_repo = CycleRepository(session)
    completed = await cycle_repo.get_last_completed_cycles(user.id, limit=24)
    active = await cycle_repo.get_active_cycle(user.id)
    cycle_length, period_length, *_ = CycleProjectionService._compute_cycle_params(
        user, completed, active_start=active.start_date if active else None
    )
    return ProfileResponse(
        name=user.name,
        email=user.email,
        average_cycle_length=cycle_length,
        average_period_length=period_length,
    )


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача для цього токена не знайдено",
        )

    if not user.name:
        updated = await user_repo.update_fields(
            user_id,
            {"name": derive_name_from_email(user.email)},
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Користувача для цього токена не знайдено",
            )
        user = updated

    return await _profile_response(user, session)


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
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
        existing = await user_repo.get_by_email(values["email"])
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already in use",
            )
        if not values.get("name") and not user.name:
            values["name"] = derive_name_from_email(values["email"])

    try:
        updated_user = await user_repo.update_fields(user_id, values)
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

    return await _profile_response(updated_user, session)
