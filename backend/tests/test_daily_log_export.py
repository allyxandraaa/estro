import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.controllers import daily_log_controller


UID = uuid.uuid4()


class _FakeDailyLogRepository:
    def __init__(self, session):
        self.session = session

    async def get_range(self, user_id, date_from, date_to):
        return self.session.logs


class _FakeCycleRepository:
    def __init__(self, session):
        self.session = session

    async def get_overlapping_range(self, user_id, date_from, date_to):
        return getattr(self.session, "cycles", [])


class _FakeUserRepository:
    def __init__(self, session):
        self.session = session

    async def get_by_id(self, user_id):
        return self.session.user


@pytest.fixture(autouse=True)
def fake_repositories(monkeypatch):
    monkeypatch.setattr(daily_log_controller, "DailyLogRepository", _FakeDailyLogRepository)
    monkeypatch.setattr(daily_log_controller, "CycleRepository", _FakeCycleRepository)
    monkeypatch.setattr(daily_log_controller, "UserRepository", _FakeUserRepository)


async def test_export_daily_logs_returns_pdf_attachment():
    session = SimpleNamespace(
        user=SimpleNamespace(name="Олена"),
        cycles=[],
        logs=[
            SimpleNamespace(
                date=date(2026, 6, 1),
                bleeding_intensity=2,
                basal_temperature=Decimal("36.70"),
                discharge_type="CREAMY",
                pain_intensity=3,
                pain_location="PELVIC",
                gastro_symptoms=["BLOATING"],
                appetite_state="NORMAL",
                stress_level=4,
                notes="Checkup note",
            )
        ],
    )

    response = await daily_log_controller.export_daily_logs(
        date_from=date(2026, 6, 1),
        date_to=date(2026, 6, 30),
        user_id=UID,
        session=session,
    )

    assert response.media_type == "application/pdf"
    assert response.headers["content-disposition"] == 'attachment; filename="cycle_log.pdf"'
    assert response.body.startswith(b"%PDF")


async def test_export_includes_cycles_when_daily_logs_are_empty():
    session = SimpleNamespace(
        user=SimpleNamespace(name="finalfix"),
        cycles=[
            SimpleNamespace(start_date=date(2026, 3, 1), end_date=date(2026, 3, 7)),
            SimpleNamespace(start_date=date(2026, 6, 18), end_date=None),
        ],
        logs=[],
    )

    response = await daily_log_controller.export_daily_logs(
        date_from=date(2025, 6, 18),
        date_to=date(2026, 6, 18),
        user_id=UID,
        session=session,
    )

    assert response.media_type == "application/pdf"
    assert response.body.startswith(b"%PDF")


async def test_export_daily_logs_rejects_range_over_366_days():
    with pytest.raises(daily_log_controller.HTTPException) as exc:
        await daily_log_controller.export_daily_logs(
            date_from=date(2025, 1, 1),
            date_to=date(2026, 1, 2),
            user_id=UID,
            session=SimpleNamespace(),
        )

    assert exc.value.status_code == 422
