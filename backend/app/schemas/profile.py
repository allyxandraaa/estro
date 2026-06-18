from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class ProfileResponse(BaseModel):
    name: str
    email: str
    average_cycle_length: Optional[int] = None
    average_period_length: Optional[int] = None
    has_cycles: bool = False

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Ім'я не може бути порожнім")
        return value
