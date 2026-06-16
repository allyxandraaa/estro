import enum
import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DischargeType(str, enum.Enum):
    DRY = "DRY"
    STICKY = "STICKY"
    CREAMY = "CREAMY"
    EGG_WHITE = "EGG_WHITE"
    ABNORMAL = "ABNORMAL"


class PainLocation(str, enum.Enum):
    NONE = "NONE"
    PELVIC = "PELVIC"
    BACK = "BACK"
    BREAST = "BREAST"
    HEAD = "HEAD"


class GastroSymptom(str, enum.Enum):
    NONE = "NONE"
    NAUSEA = "NAUSEA"
    CONSTIPATION = "CONSTIPATION"
    DIARRHEA = "DIARRHEA"
    BLOATING = "BLOATING"


class AppetiteState(str, enum.Enum):
    NORMAL = "NORMAL"
    INCREASED = "INCREASED"
    DECREASED = "DECREASED"
    CRAVING_SWEET = "CRAVING_SWEET"
    CRAVING_SALTY = "CRAVING_SALTY"


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Кровотеча та БТТ
    bleeding_intensity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    basal_temperature: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)

    # Виділення
    discharge_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Біль
    pain_intensity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pain_location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # ШКТ (масив)
    gastro_symptoms: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Апетит
    appetite_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Загальне
    stress_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)