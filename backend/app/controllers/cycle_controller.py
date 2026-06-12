from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.cycle_service import CycleService
from app.services.auth_service import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/cycles", tags=["cycles"])


class CycleDateRequest:
    def __init__(self, date: date):
        self.date = date


from pydantic import BaseModel

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
