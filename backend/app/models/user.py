import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Date, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    average_cycle_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_period_length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_period_date: Mapped[Optional[date]] = mapped_column(
    Date,
    nullable=True
    )

    is_calculated_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
