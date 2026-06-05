from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OnboardingRequest(BaseModel):
    cycle_length: Optional[int] = Field(None, ge=1, le=90)
    period_length: Optional[int] = Field(None, ge=1, le=20)
    last_period_date: Optional[date] = None

    @field_validator("last_period_date")
    @classmethod
    def must_be_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("Дата останньої менструації не може бути в майбутньому")
        return v

    @model_validator(mode="after")
    def period_shorter_than_cycle(self) -> "OnboardingRequest":
        if (
            self.cycle_length is not None
            and self.period_length is not None
            and self.period_length >= self.cycle_length
        ):
            raise ValueError(
                "Тривалість менструації має бути меншою за тривалість циклу"
            )
        return self
