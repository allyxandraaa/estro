from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_session
from app.dependencies.auth import get_current_user_id
from app.repositories.cycle_repository import CycleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.cycles import CalendarViewResponse, StartCycleRequest, StartCycleResponse
from app.services.cycle_projection_service import CycleProjectionService
from app.services.cycle_service import CycleService

router = APIRouter(prefix="/api/cycles", tags=["Cycles"])


def _get_cycle_service(session: AsyncSession = Depends(get_session)) -> CycleService:
    return CycleService(session)


def _get_projection_service(session: AsyncSession = Depends(get_session)) -> CycleProjectionService:
    return CycleProjectionService(
        user_repository=UserRepository(session),
        cycle_repository=CycleRepository(session),
    )


@router.get("/calendar-view", response_model=CalendarViewResponse)
async def get_calendar_view(
    month: Annotated[int, Field(ge=1, le=12)],
    year: Annotated[int, Field(ge=2000, le=2100)],
    user_id: UUID = Depends(get_current_user_id),
    service: CycleProjectionService = Depends(_get_projection_service),
):
    return await service.get_calendar_month(user_id, month, year)


@router.post("/start", status_code=status.HTTP_201_CREATED, response_model=StartCycleResponse)
async def start_cycle(
    body: StartCycleRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: CycleService = Depends(_get_cycle_service),
    session: AsyncSession = Depends(get_session),
):
    cycle_repo = CycleRepository(session)
    user_repo = UserRepository(session)

    active_cycle = await cycle_repo.get_active_cycle(user_id)
    if active_cycle:
        if active_cycle.start_date < body.date:
            await cycle_repo.close_cycle(active_cycle, body.date)
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Є відкритий цикл з датою початку не раніше нової дати",
            )

    cycle = await cycle_repo.create_cycle(user_id, body.date)
    await user_repo.update_fields(user_id, {"last_period_date": body.date})

    return StartCycleResponse(
        id=str(cycle.id),
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )
