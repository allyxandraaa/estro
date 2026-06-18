from datetime import date, timedelta
from io import BytesIO
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user_id
from app.repositories.daily_log_repository import DailyLogRepository
from app.repositories.user_repository import UserRepository
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


@router.get("/export")
async def export_daily_logs_pdf(
    date_from: date,
    date_to: date,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    if date_to < date_from:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="date_to не може бути раніше date_from")
    if (date_to - date_from).days + 1 > 366:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Максимальний діапазон — 366 днів")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    user_name = user.name if user and user.name else "Користувач"

    logs = await DailyLogRepository(session).get_range(user_id, date_from, date_to)
    logs_by_date = {log.date: log for log in logs}

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Щоденник циклу — {user_name}", styles["Title"]))
    story.append(Paragraph(f"{date_from} — {date_to}", styles["Normal"]))
    story.append(Spacer(1, 12))

    current = date_from
    while current <= date_to:
        log = logs_by_date.get(current)
        if log:
            story.append(Paragraph(f"<b>{current}</b>", styles["Heading2"]))
            fields = [
                ("Кровотеча", log.bleeding_intensity),
                ("Базальна температура", log.basal_temperature),
                ("Виділення", log.discharge_type),
                ("Біль (інтенсивність)", log.pain_intensity),
                ("Локалізація болю", log.pain_location),
                ("ШКТ симптоми", ", ".join(log.gastro_symptoms) if log.gastro_symptoms else None),
                ("Апетит", log.appetite_state),
                ("Стрес", log.stress_level),
                ("Нотатки", log.notes),
            ]
            for label, value in fields:
                if value is not None:
                    story.append(Paragraph(f"{label}: {value}", styles["Normal"]))
            story.append(Spacer(1, 8))
        current += timedelta(days=1)

    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cycle_log.pdf"},
    )