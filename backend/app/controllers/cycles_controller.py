from datetime import timedelta
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
        user = await user_repo.get_by_id(user_id)
        period_length = (user.average_period_length if user else None) or 5
        expected_end = active_cycle.start_date + timedelta(days=period_length - 1)

        if active_cycle.start_date <= body.date <= expected_end:
            # Корекція: нова дата всередині очікуваного вікна — правимо старт
            cycle = await cycle_repo.update_start(active_cycle, body.date)
            await user_repo.update_fields(user_id, {"last_period_date": body.date})
            return StartCycleResponse(
                id=str(cycle.id),
                start_date=cycle.start_date,
                end_date=cycle.end_date,
            )

        if body.date < active_cycle.start_date:
            # Історична дата: створюємо завершений цикл, не чіпаємо активний
            hist_end = min(
                body.date + timedelta(days=period_length - 1),
                active_cycle.start_date - timedelta(days=1),
            )
            hist_cycle = await cycle_repo.create_cycle(user_id, body.date)
            await cycle_repo.close_cycle(hist_cycle, hist_end)
            return StartCycleResponse(
                id=str(hist_cycle.id),
                start_date=hist_cycle.start_date,
                end_date=hist_cycle.end_date,
            )

        # Новий цикл: закриваємо попередній і відкриваємо новий атомарно
        implied_end = min(expected_end, body.date - timedelta(days=1))
        cycle = await cycle_repo.close_and_create_cycle(active_cycle, implied_end, user_id, body.date)
    else:
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

    next_cycle = await cycle_repo.get_next_cycle(user_id, active_cycle.start_date)
    if next_cycle and body.date >= next_cycle.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Дата завершення перекривається з наступним циклом",
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


@router.patch("/{cycle_id}/end", status_code=status.HTTP_200_OK, response_model=StartCycleResponse)
async def update_cycle_end(
    cycle_id: UUID,
    body: EndCycleRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    cycle_repo = CycleRepository(session)
    cycle = await cycle_repo.get_by_id(cycle_id, user_id)
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Цикл не знайдено")
    if body.date < cycle.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Дата завершення не може бути раніше дати початку циклу",
        )
    updated = await cycle_repo.close_cycle(cycle, body.date)

    user_repo = UserRepository(session)
    completed = await cycle_repo.get_last_completed_cycles(user_id, limit=6)
    if completed:
        lengths = [(c.end_date - c.start_date).days + 1 for c in completed if c.end_date]
        if lengths:
            await user_repo.update_fields(user_id, {"average_period_length": round(sum(lengths) / len(lengths))})

    return StartCycleResponse(
        id=str(updated.id),
        start_date=updated.start_date,
        end_date=updated.end_date,
    )


@router.delete("/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cycle(
    cycle_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    cycle_repo = CycleRepository(session)
    user_repo = UserRepository(session)

    cycle = await cycle_repo.get_by_id(cycle_id, user_id)
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Цикл не знайдено")

    await cycle_repo.delete_cycle(cycle)

    # Перераховуємо середню тривалість менструації
    completed = await cycle_repo.get_last_completed_cycles(user_id, limit=6)
    updates: dict = {}
    if completed:
        lengths = [(c.end_date - c.start_date).days + 1 for c in completed if c.end_date]
        if lengths:
            updates["average_period_length"] = round(sum(lengths) / len(lengths))

    # Оновлюємо last_period_date з останнього циклу, що залишився
    active = await cycle_repo.get_active_cycle(user_id)
    if active:
        updates["last_period_date"] = active.start_date
    elif completed:
        updates["last_period_date"] = completed[0].start_date
    else:
        updates["last_period_date"] = None

    if updates:
        await user_repo.update_fields(user_id, updates)
