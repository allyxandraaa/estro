from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user_id
from app.schemas.daily_logs import DailyLogRequest, DailyLogResponse
from app.services.daily_log_service import DailyLogService

router = APIRouter(prefix="/api/daily-logs", tags=["DailyLogs"])


def _get_service(session: AsyncSession = Depends(get_session)) -> DailyLogService:
    return DailyLogService(session)


def _to_response(log) -> DailyLogResponse:
    return DailyLogResponse.model_validate(log, from_attributes=True)


def _to_fields(body: DailyLogRequest) -> dict:
    return body.model_dump(mode="json", exclude={"date"})


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DailyLogResponse)
async def upsert_daily_log(
    body: DailyLogRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    log = await service.upsert(user_id, body.date, **_to_fields(body))
    return _to_response(log)


@router.get("", response_model=DailyLogResponse)
async def get_daily_log(
    date: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    log = await service.get_by_date(user_id, date)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено")
    return _to_response(log)


@router.get("/range", response_model=list[DailyLogResponse])
async def get_daily_logs_range(
    date_from: date,
    date_to: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    try:
        logs = await service.get_range(user_id, date_from, date_to)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return [_to_response(log) for log in logs]


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_log(
    date: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    deleted = await service.delete(user_id, date)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено")