from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class ProfileResponse(BaseModel):
    name: str
    email: str
    average_cycle_length: Optional[int] = None
    average_period_length: Optional[int] = None

    model_config = {"from_attributes": True}


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    average_cycle_length: Optional[int] = Field(None, ge=1, le=90)
    average_period_length: Optional[int] = Field(None, ge=1, le=20)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Ім'я не може бути порожнім")
        return value

    @model_validator(mode="after")
    def validate_profile_values(self) -> "ProfileUpdateRequest":
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError("Поля профілю не можуть бути null")

        if (
            self.average_cycle_length is not None
            and self.average_period_length is not None
            and self.average_period_length >= self.average_cycle_length
        ):
            raise ValueError(
                "Тривалість менструації має бути меншою за тривалість циклу"
            )
        return self
