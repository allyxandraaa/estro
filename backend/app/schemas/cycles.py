from datetime import date
from typing import Optional

from pydantic import BaseModel, field_validator


class CalendarDaySchema(BaseModel):
    date: str
    is_menstruation: bool
    is_menstruation_predicted: bool
    is_ovulation_predicted: bool
    is_fertile_window: bool = False


class ActiveCycleSchema(BaseModel):
    id: str
    start_date: date
    end_date: Optional[date] = None


class CalendarViewResponse(BaseModel):
    days: list[CalendarDaySchema]
    current_phase: str
    phase_subtitle: str
    active_cycle: Optional[ActiveCycleSchema] = None
    completed_cycles: list[ActiveCycleSchema] = []


class StartCycleRequest(BaseModel):
    date: date

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: date) -> date:
        from datetime import date as date_type, timedelta
        # +1 день буфер для користувачів у часових поясах UTC+ (сервер у UTC)
        if v > date_type.today() + timedelta(days=1):
            raise ValueError("Дата не може бути в майбутньому")
        return v


EndCycleRequest = StartCycleRequest


class StartCycleResponse(BaseModel):
    id: str
    start_date: date
    end_date: Optional[date] = None
