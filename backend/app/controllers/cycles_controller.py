from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_session
from app.dependencies.auth import get_current_user_id
from app.repositories.cycle_repository import CycleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.cycles import CalendarViewResponse, EndCycleRequest, StartCycleRequest, StartCycleResponse
from app.services.cycle_projection_service import CycleProjectionService

router = APIRouter(prefix="/api/cycles", tags=["Cycles"])


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
    session: AsyncSession = Depends(get_session),
):
    cycle_repo = CycleRepository(session)
    user_repo = UserRepository(session)

    active_cycle = await cycle_repo.get_active_cycle(user_id)
    if active_cycle:
        # Будь-яка зміна дати активного циклу — корекція, а не новий цикл
        cycle = await cycle_repo.update_start(active_cycle, body.date)
        await user_repo.update_fields(user_id, {"last_period_date": body.date})
        return StartCycleResponse(
            id=str(cycle.id),
            start_date=cycle.start_date,
            end_date=cycle.end_date,
        )

    cycle = await cycle_repo.create_cycle(user_id, body.date)
    await user_repo.update_fields(user_id, {"last_period_date": body.date})

    return StartCycleResponse(
        id=str(cycle.id),
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )


@router.post("/end", status_code=status.HTTP_200_OK, response_model=StartCycleResponse)
async def end_cycle(
    body: EndCycleRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    cycle_repo = CycleRepository(session)

    active_cycle = await cycle_repo.get_active_cycle(user_id)
    if not active_cycle:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Немає відкритого циклу",
        )
    if body.date < active_cycle.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Дата завершення не може бути раніше дати початку циклу",
        )

    cycle = await cycle_repo.close_cycle(active_cycle, body.date)

    # Оновлюємо середню тривалість менструації з реальних даних
    user_repo = UserRepository(session)
    completed = await cycle_repo.get_last_completed_cycles(user_id, limit=6)
    if completed:
        lengths = [(c.end_date - c.start_date).days + 1 for c in completed if c.end_date]
        if lengths:
            await user_repo.update_fields(user_id, {"average_period_length": round(sum(lengths) / len(lengths))})

    return StartCycleResponse(
        id=str(cycle.id),
        start_date=cycle.start_date,
        end_date=cycle.end_date,
    )
