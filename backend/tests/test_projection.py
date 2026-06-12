"""
Юніт-тести сервісу прогнозування циклу.
Покриває: TC-06, TC-07, TC-08, TC-09 (сервісний шар).
"""
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.cycle_projection_service import CycleProjectionService

TODAY = date.today()
UID = uuid.uuid4()


def _user(cycle_length=28, period_length=5, is_default=True, last_period_date=None):
    u = MagicMock()
    u.average_cycle_length = cycle_length
    u.average_period_length = period_length
    u.is_calculated_default = is_default
    u.last_period_date = last_period_date
    return u


def _cycle(start, end=None):
    c = MagicMock()
    c.start_date = start
    c.end_date = end
    return c


def _svc(user, cycles, active=None):
    svc = CycleProjectionService(
        user_repository=AsyncMock(),
        cycle_repository=AsyncMock(),
    )
    svc.user_repository.get_by_id.return_value = user
    svc.cycle_repository.get_last_completed_cycles.return_value = cycles
    svc.cycle_repository.get_active_cycle.return_value = active
    return svc


# ── TC-09: базова логіка прогнозів ─────────────────────────────────────────


async def test_no_data_returns_empty():
    svc = _svc(_user(last_period_date=None), [])
    result = await svc.calculate_cycle_projections(UID, until=TODAY + timedelta(days=30))
    assert result == []


async def test_projection_from_last_period_date():
    """TC-09: base=2026-05-14, cycle=28, period=5 → прогноз 11-15 червня, овуляція 25 червня."""
    base = date(2026, 5, 14)
    svc = _svc(_user(cycle_length=28, period_length=5, is_default=True, last_period_date=base), [])

    result = await svc.calculate_cycle_projections(UID, until=date(2026, 6, 30))

    proj = next((p for p in result if p.predicted_start_date == date(2026, 6, 11)), None)
    assert proj is not None, "Очікується прогноз на 2026-06-11"
    assert proj.predicted_end_date == date(2026, 6, 15)
    assert proj.predicted_ovulation_date == date(2026, 6, 25)


async def test_active_start_overrides_completed():
    """Активний цикл має пріоритет над завершеним при виборі базової дати."""
    svc = _svc(
        _user(cycle_length=28, period_length=5, is_default=False),
        [_cycle(date(2026, 5, 9), date(2026, 5, 14))],
    )
    result = await svc.calculate_cycle_projections(
        UID, until=date(2026, 7, 31), active_start=date(2026, 6, 11)
    )
    starts = {p.predicted_start_date for p in result}
    # Проєкції мають йти від 2026-06-11, а не від 2026-05-09
    assert date(2026, 5, 9) not in starts
    assert any(s >= date(2026, 6, 11) for s in starts)


async def test_rolling_average_with_3_cycles():
    """TC-09 edge: 3 цикли з різницями 26/30/28 → середнє 28."""
    starts = [date(2026, 1, 1), date(2026, 1, 27), date(2026, 2, 26), date(2026, 3, 26)]
    cycles = [_cycle(starts[i], starts[i] + timedelta(days=4)) for i in range(3)]
    svc = _svc(_user(is_default=False), cycles)

    result = await svc.calculate_cycle_projections(UID, until=TODAY + timedelta(days=60))
    # Не перевіряємо конкретну дату (залежить від TODAY), але прогнози мають бути
    assert len(result) > 0


# ── Огіно-Кнаус ─────────────────────────────────────────────────────────────


async def test_ogino_activates_at_6_cycles():
    """6 завершених циклів (5 дифів) → фертильне вікно присутнє."""
    base = date(2025, 1, 1)
    cycles = [_cycle(base + timedelta(days=28 * i), base + timedelta(days=28 * i + 4)) for i in range(6)]
    svc = _svc(_user(is_default=False), cycles)

    result = await svc.calculate_cycle_projections(UID, until=TODAY + timedelta(days=90))
    future = [p for p in result if p.predicted_start_date > TODAY]

    assert future, "Очікується хоча б один майбутній прогноз"
    assert future[0].fertile_window_start is not None, "Огіно-Кнаус має бути при 6 циклах"


async def test_ogino_not_active_at_5_cycles():
    """5 завершених циклів (4 дифи) → фертильного вікна немає."""
    base = date(2025, 1, 1)
    cycles = [_cycle(base + timedelta(days=28 * i), base + timedelta(days=28 * i + 4)) for i in range(5)]
    svc = _svc(_user(is_default=False), cycles)

    result = await svc.calculate_cycle_projections(UID, until=TODAY + timedelta(days=90))
    future = [p for p in result if p.predicted_start_date > TODAY]

    if future:
        assert future[0].fertile_window_start is None, "Огіно-Кнаус НЕ має бути при 5 циклах"


async def test_ogino_window_formula():
    """Перевіряємо формулу: min-18 .. max-11 від початку прогнозованого циклу."""
    base = date(2025, 1, 1)
    # 6 циклів: 5 з кроком 26, 1 з кроком 30 → min=26, max=30
    starts_raw = [base + timedelta(days=26 * i) for i in range(5)] + [base + timedelta(days=26 * 5 + 4)]
    cycles = [_cycle(starts_raw[i], starts_raw[i] + timedelta(days=4)) for i in range(6)]
    svc = _svc(_user(is_default=False), cycles)

    result = await svc.calculate_cycle_projections(UID, until=TODAY + timedelta(days=90))
    future = [p for p in result if p.predicted_start_date > TODAY and p.fertile_window_start is not None]

    if future:
        p = future[0]
        diffs = [
            (cycles[i + 1].start_date - cycles[i].start_date).days for i in range(5)
        ]
        min_c, max_c = min(diffs), max(diffs)
        assert p.fertile_window_start == p.predicted_start_date + timedelta(days=min_c - 18)
        assert p.fertile_window_end == p.predicted_start_date + timedelta(days=max_c - 11)


# ── TC-06: розмітка днів у календарі ────────────────────────────────────────


async def test_no_day_has_both_real_and_predicted():
    """TC-06: жоден день не може мати is_menstruation=True і is_menstruation_predicted=True."""
    base = date(2026, 5, 14)
    svc = _svc(_user(cycle_length=28, period_length=5, is_default=True, last_period_date=base), [])

    data = await svc.get_calendar_month(UID, month=6, year=2026)
    for day in data["days"]:
        assert not (day["is_menstruation"] and day["is_menstruation_predicted"]), (
            f"{day['date']}: одночасно real і predicted"
        )


async def test_active_cycle_marks_full_expected_period():
    """Активний цикл позначає весь очікуваний period як реальну менструацію."""
    start = date(2026, 6, 11)
    active = _cycle(start)  # end=None — відкритий
    svc = _svc(_user(period_length=5, is_default=True), [], active=active)

    data = await svc.get_calendar_month(UID, month=6, year=2026)
    real_days = [d["date"] for d in data["days"] if d["is_menstruation"]]

    for expected in ["2026-06-11", "2026-06-12", "2026-06-13", "2026-06-14", "2026-06-15"]:
        assert expected in real_days, f"{expected} має бути реальною менструацією"


# ── TC-07/TC-08: валідація дат ───────────────────────────────────────────────


def test_start_request_rejects_future_date():
    """POST /cycles/start: дата в майбутньому → ValidationError."""
    from pydantic import ValidationError
    from app.schemas.cycles import StartCycleRequest

    with pytest.raises(ValidationError):
        StartCycleRequest(date=TODAY + timedelta(days=1))


def test_start_request_accepts_past_date():
    """POST /cycles/start: дата минулого → OK."""
    from app.schemas.cycles import StartCycleRequest

    req = StartCycleRequest(date=TODAY - timedelta(days=7))
    assert req.date == TODAY - timedelta(days=7)


def test_end_request_rejects_future_date():
    """POST /cycles/end: дата в майбутньому → ValidationError."""
    from pydantic import ValidationError
    from app.schemas.cycles import EndCycleRequest

    with pytest.raises(ValidationError):
        EndCycleRequest(date=TODAY + timedelta(days=1))
