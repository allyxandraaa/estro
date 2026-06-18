from datetime import date
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


DischargeType = Literal["DRY", "STICKY", "CREAMY", "EGG_WHITE", "ABNORMAL"]
PainLocation = Literal["NONE", "PELVIC", "BACK", "BREAST", "HEAD"]
GastroSymptom = Literal["NONE", "NAUSEA", "CONSTIPATION", "DIARRHEA", "BLOATING"]
AppetiteState = Literal["NORMAL", "INCREASED", "DECREASED", "CRAVING_SWEET", "CRAVING_SALTY"]


class DailyLogPayload(BaseModel):
    bleeding_intensity: Optional[int] = Field(None, ge=0, le=5)
    basal_temperature: Optional[Decimal] = Field(None, ge=30, le=45, decimal_places=2)
    discharge_type: Optional[DischargeType] = None
    pain_intensity: Optional[int] = Field(None, ge=0, le=10)
    pain_location: Optional[list[PainLocation]] = None
    gastro_symptoms: Optional[list[GastroSymptom]] = None
    appetite_state: Optional[AppetiteState] = None
    stress_level: Optional[int] = Field(None, ge=0, le=10)
    notes: Optional[str] = Field(None, max_length=2000)

    @field_validator("pain_location", mode="before")
    @classmethod
    def normalize_pain_location(cls, value):
        if value is None or isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


class DailyLogResponse(DailyLogPayload):
    date: date

    model_config = {"from_attributes": True}
