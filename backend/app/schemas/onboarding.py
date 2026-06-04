from pydantic import BaseModel
from datetime import date
from typing import Optional


class OnboardingRequest(BaseModel):
    cycle_length: Optional[int] = None
    period_length: Optional[int] = None
    # TODO: додати last_period_date після міграції від Data Engineer
