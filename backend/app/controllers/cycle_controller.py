from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.repositories.cycle_repository import CycleRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import get_current_user
from app.services.cycle_projection_service import CycleProjectionService
from app.services.cycle_service import CycleService

router = APIRouter(prefix="/api/cycles", tags=["cycles"])


class CycleDateSchema(BaseModel):
    date: date


@router.post("/start")
async def start_cycle(
    body: CycleDateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CycleService(db)
    try:
        cycle = await service.start_cycle(current_user.id, body.date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": str(cycle.id), "start_date": cycle.start_date}


@router.post("/end")
async def end_cycle(
    body: CycleDateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CycleService(db)
    try:
        cycle = await service.end_cycle(current_user.id, body.date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": str(cycle.id), "start_date": cycle.start_date, "end_date": cycle.end_date}


@router.get("/calendar-view")
async def get_calendar_view(
    month: int,
    year: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CycleProjectionService(
        user_repository=UserRepository(db),
        cycle_repository=CycleRepository(db),
    )
    return await service.get_calendar_month(current_user.id, month, year)
