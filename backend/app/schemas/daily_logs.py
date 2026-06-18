from datetime import date as date_type, timedelta
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.daily_log import AppetiteState, DischargeType, GastroSymptom, PainLocation


class DailyLogRequest(BaseModel):
    date: date_type

    bleeding_intensity: Optional[int] = Field(None, ge=0, le=10)
    basal_temperature: Optional[float] = Field(None, ge=30, le=45)

    discharge_type: Optional[DischargeType] = None

    pain_intensity: Optional[int] = Field(None, ge=0, le=10)
    pain_location: Optional[PainLocation] = None

    gastro_symptoms: Optional[list[GastroSymptom]] = None

    appetite_state: Optional[AppetiteState] = None

    stress_level: Optional[int] = Field(None, ge=0, le=10)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("date")
    @classmethod
    def date_not_in_future(cls, v: date_type) -> date_type:
        if v > date_type.today() + timedelta(days=1):
            raise ValueError("Дата не може бути в майбутньому")
        return v


class DailyLogResponse(BaseModel):
    id: str
    date: date_type

    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v) -> str:
        return str(v)

    bleeding_intensity: Optional[int] = None
    basal_temperature: Optional[float] = None

    discharge_type: Optional[str] = None

    pain_intensity: Optional[int] = None
    pain_location: Optional[str] = None

    gastro_symptoms: Optional[list[str]] = None

    appetite_state: Optional[str] = None

    stress_level: Optional[int] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True