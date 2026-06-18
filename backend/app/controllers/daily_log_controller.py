from datetime import date
from io import BytesIO
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dependencies.auth import get_current_user_id
from app.repositories.cycle_repository import CycleRepository
from app.repositories.daily_log_repository import DailyLogRepository
from app.repositories.user_repository import UserRepository
from app.schemas.daily_log import DailyLogPayload, DailyLogRequest, DailyLogResponse
from app.services.daily_log_service import DailyLogService

router = APIRouter(prefix="/api/daily-logs", tags=["Daily logs"])

FONT_NAME = "EstroSans"

TEXT = {
    "title": "\u0429\u043e\u0434\u0435\u043d\u043d\u0438\u043a \u0446\u0438\u043a\u043b\u0443 \u2014 {user_name}",
    "empty": "\u041d\u0435\u043c\u0430\u0454 \u0437\u0430\u043f\u0438\u0441\u0456\u0432 \u0437\u0430 \u043e\u0431\u0440\u0430\u043d\u0438\u0439 \u043f\u0435\u0440\u0456\u043e\u0434.",
    "cycles_title": "\u041f\u043e\u0437\u043d\u0430\u0447\u0435\u043d\u0456 \u043c\u0435\u043d\u0441\u0442\u0440\u0443\u0430\u0446\u0456\u0457",
    "logs_title": "\u0429\u043e\u0434\u0435\u043d\u043d\u0456 \u0437\u0430\u043f\u0438\u0441\u0438",
    "cycle_start": "\u041f\u043e\u0447\u0430\u0442\u043e\u043a",
    "cycle_end": "\u041a\u0456\u043d\u0435\u0446\u044c",
    "cycle_duration": "\u0422\u0440\u0438\u0432\u0430\u043b\u0456\u0441\u0442\u044c",
    "cycle_ongoing": "\u0422\u0440\u0438\u0432\u0430\u0454",
    "days": "\u0434\u043d.",
    "date": "\u0414\u0430\u0442\u0430",
    "bleeding": "\u041a\u0440\u043e\u0432\u043e\u0442\u0435\u0447\u0430",
    "temperature": "\u0411\u0430\u0437\u0430\u043b\u044c\u043d\u0430 \u0442\u0435\u043c\u043f\u0435\u0440\u0430\u0442\u0443\u0440\u0430",
    "discharge": "\u0412\u0438\u0434\u0456\u043b\u0435\u043d\u043d\u044f",
    "pain": "\u0411\u0456\u043b\u044c",
    "gastro": "\u0428\u041a\u0422",
    "appetite": "\u0410\u043f\u0435\u0442\u0438\u0442",
    "stress": "\u0421\u0442\u0440\u0435\u0441",
    "notes": "\u041d\u043e\u0442\u0430\u0442\u043a\u0438",
}

VALUE_LABELS = {
    "DRY": "\u0421\u0443\u0445\u043e",
    "STICKY": "\u041b\u0438\u043f\u043a\u0456",
    "CREAMY": "\u041a\u0440\u0435\u043c\u043e\u0432\u0456",
    "EGG_WHITE": "\u042f\u0454\u0447\u043d\u0438\u0439 \u0431\u0456\u043b\u043e\u043a",
    "ABNORMAL": "\u041d\u0435\u0437\u0432\u0438\u0447\u043d\u0456",
    "NONE": "\u041d\u0435\u043c\u0430\u0454",
    "PELVIC": "\u0422\u0430\u0437",
    "BACK": "\u0421\u043f\u0438\u043d\u0430",
    "BREAST": "\u0413\u0440\u0443\u0434\u0438",
    "HEAD": "\u0413\u043e\u043b\u043e\u0432\u0430",
    "NAUSEA": "\u041d\u0443\u0434\u043e\u0442\u0430",
    "CONSTIPATION": "\u0417\u0430\u043a\u0440\u0435\u043f",
    "DIARRHEA": "\u0414\u0456\u0430\u0440\u0435\u044f",
    "BLOATING": "\u0417\u0434\u0443\u0442\u0442\u044f",
    "NORMAL": "\u041d\u043e\u0440\u043c\u0430\u043b\u044c\u043d\u0438\u0439",
    "INCREASED": "\u041f\u0456\u0434\u0432\u0438\u0449\u0435\u043d\u0438\u0439",
    "DECREASED": "\u0417\u043d\u0438\u0436\u0435\u043d\u0438\u0439",
    "CRAVING_SWEET": "\u0422\u044f\u0433\u0430 \u0434\u043e \u0441\u043e\u043b\u043e\u0434\u043a\u043e\u0433\u043e",
    "CRAVING_SALTY": "\u0422\u044f\u0433\u0430 \u0434\u043e \u0441\u043e\u043b\u043e\u043d\u043e\u0433\u043e",
}


def _get_service(session: AsyncSession = Depends(get_session)) -> DailyLogService:
    return DailyLogService(session)


def _register_pdf_font() -> str:
    if FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return FONT_NAME

    font_paths = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibri.ttf"),
    ]

    for font_path in font_paths:
        if not font_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(FONT_NAME, str(font_path)))
            return FONT_NAME
        except Exception:
            continue

    raise RuntimeError("No Unicode font found for PDF export")


def _format_value(value) -> str:
    if value is None:
        return "-"
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value) if value else "-"
    text = str(value)
    if "," in text:
        return ", ".join(_format_value(item.strip()) for item in text.split(",") if item.strip())
    return VALUE_LABELS.get(text, text)


def _serialize_fields(fields: dict) -> dict:
    if isinstance(fields.get("pain_location"), list):
        fields["pain_location"] = ",".join(fields["pain_location"]) or None
    return fields


def _to_daily_log_response(log) -> DailyLogResponse:
    return DailyLogResponse.model_validate(log)


def _build_pdf(user_name: str, date_from: date, date_to: date, logs: list, cycles: list | None = None) -> bytes:
    font_name = _register_pdf_font()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "EstroTitle",
        parent=styles["Title"],
        fontName=font_name,
        fontSize=18,
        leading=24,
        alignment=0,
        textColor=colors.HexColor("#111111"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "EstroSubtitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#555555"),
        spaceAfter=14,
    )
    label_style = ParagraphStyle(
        "EstroLabel",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#555555"),
    )
    value_style = ParagraphStyle(
        "EstroValue",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#111111"),
    )
    date_style = ParagraphStyle(
        "EstroDate",
        parent=value_style,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#000000"),
    )
    section_style = ParagraphStyle(
        "EstroSection",
        parent=styles["Heading2"],
        fontName=font_name,
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#111111"),
        spaceBefore=8,
        spaceAfter=7,
    )

    story = [
        Paragraph(TEXT["title"].format(user_name=user_name), title_style),
        Paragraph(f"{date_from.isoformat()} \u2014 {date_to.isoformat()}", subtitle_style),
    ]

    cycles = cycles or []
    if cycles:
        story.append(Paragraph(TEXT["cycles_title"], section_style))
        rows = [[
            Paragraph(TEXT["cycle_start"], label_style),
            Paragraph(TEXT["cycle_end"], label_style),
            Paragraph(TEXT["cycle_duration"], label_style),
        ]]
        for cycle in cycles:
            if cycle.end_date:
                duration = f"{(cycle.end_date - cycle.start_date).days + 1} {TEXT['days']}"
                end_date = cycle.end_date.isoformat()
            else:
                duration = TEXT["cycle_ongoing"]
                end_date = "-"
            rows.append([
                Paragraph(cycle.start_date.isoformat(), value_style),
                Paragraph(end_date, value_style),
                Paragraph(duration, value_style),
            ])
        table = Table(rows, colWidths=[60 * mm, 60 * mm, 62 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f1f1")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfcfcf")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e3e3e3")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([table, Spacer(1, 6 * mm)])

    if logs:
        story.append(Paragraph(TEXT["logs_title"], section_style))
    elif not cycles:
        story.append(Paragraph(TEXT["empty"], value_style))

    for log in logs:
        pain = f"{_format_value(log.pain_intensity)} / {_format_value(log.pain_location)}"
        rows = [
            [Paragraph(TEXT["date"], label_style), Paragraph(log.date.isoformat(), date_style)],
            [Paragraph(TEXT["bleeding"], label_style), Paragraph(_format_value(log.bleeding_intensity), value_style)],
            [Paragraph(TEXT["temperature"], label_style), Paragraph(_format_value(log.basal_temperature), value_style)],
            [Paragraph(TEXT["discharge"], label_style), Paragraph(_format_value(log.discharge_type), value_style)],
            [Paragraph(TEXT["pain"], label_style), Paragraph(pain, value_style)],
            [Paragraph(TEXT["gastro"], label_style), Paragraph(_format_value(log.gastro_symptoms), value_style)],
            [Paragraph(TEXT["appetite"], label_style), Paragraph(_format_value(log.appetite_state), value_style)],
            [Paragraph(TEXT["stress"], label_style), Paragraph(_format_value(log.stress_level), value_style)],
            [Paragraph(TEXT["notes"], label_style), Paragraph(_format_value(log.notes), value_style)],
        ]
        table = Table(rows, colWidths=[48 * mm, 134 * mm], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f1f1")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfcfcf")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e3e3e3")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, -1), font_name),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(KeepTogether([table, Spacer(1, 5 * mm)]))

    doc.build(story)
    return buffer.getvalue()


@router.get("/export")
async def export_daily_logs(
    date_from: date,
    date_to: date,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    if date_to < date_from:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_to must be greater than or equal to date_from",
        )
    if (date_to - date_from).days + 1 > 366:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Date range cannot exceed 366 days",
        )

    user = await UserRepository(session).get_by_id(user_id)
    logs = await DailyLogRepository(session).get_range(user_id, date_from, date_to)
    cycles = await CycleRepository(session).get_overlapping_range(user_id, date_from, date_to)
    pdf = _build_pdf(user.name if user else "", date_from, date_to, logs, cycles)

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="cycle_log.pdf"'},
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DailyLogResponse)
async def create_or_update_daily_log(
    body: DailyLogRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    values = _serialize_fields(body.model_dump(mode="json", exclude={"date"}))
    log = await service.upsert(user_id, body.date, **values)
    return _to_daily_log_response(log)


@router.get("", response_model=DailyLogResponse)
async def get_daily_log_by_query(
    date: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    log = await service.get_by_date(user_id, date)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Daily log not found")
    return _to_daily_log_response(log)


@router.get("/range", response_model=list[DailyLogResponse])
async def get_daily_logs_range(
    date_from: date,
    date_to: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    try:
        logs = await service.get_range(user_id, date_from, date_to)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return [_to_daily_log_response(log) for log in logs]


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_log_by_query(
    date: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    deleted = await service.delete(user_id, date)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Daily log not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{log_date}", response_model=DailyLogResponse | None)
async def get_daily_log(
    log_date: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    log = await service.get_by_date(user_id, log_date)
    return _to_daily_log_response(log) if log else None


@router.put("/{log_date}", response_model=DailyLogResponse)
async def upsert_daily_log(
    log_date: date,
    payload: DailyLogPayload,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    values = _serialize_fields(payload.model_dump(exclude_unset=True))
    log = await service.upsert(user_id, log_date, **values)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Daily log was not saved",
        )
    return _to_daily_log_response(log)


@router.delete("/{log_date}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_log(
    log_date: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyLogService = Depends(_get_service),
):
    await service.delete(user_id, log_date)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
