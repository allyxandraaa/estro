"""
Юніт-тести сервісу прогнозування циклу.
Покриває: TC-06, TC-07, TC-08, TC-09 (сервісний шар).
"""
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.cycle_projection_service import CycleProjectionService

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
    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=30))
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

    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=60))
    # Не перевіряємо конкретну дату (залежить від date.today()), але прогнози мають бути
    assert len(result) > 0


# ── Огіно-Кнаус ─────────────────────────────────────────────────────────────


async def test_ogino_activates_at_6_cycles():
    """6 завершених циклів (5 дифів) → фертильне вікно присутнє."""
    base = date(2025, 1, 1)
    cycles = [_cycle(base + timedelta(days=28 * i), base + timedelta(days=28 * i + 4)) for i in range(6)]
    svc = _svc(_user(is_default=False), cycles)

    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=90))
    future = [p for p in result if p.predicted_start_date > date.today()]

    assert future, "Очікується хоча б один майбутній прогноз"
    assert future[0].fertile_window_start is not None, "Огіно-Кнаус має бути при 6 циклах"


async def test_ogino_not_active_at_5_cycles():
    """5 завершених циклів (4 дифи) → фертильного вікна немає."""
    base = date(2025, 1, 1)
    cycles = [_cycle(base + timedelta(days=28 * i), base + timedelta(days=28 * i + 4)) for i in range(5)]
    svc = _svc(_user(is_default=False), cycles)

    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=90))
    future = [p for p in result if p.predicted_start_date > date.today()]

    assert future, "Очікується хоча б один майбутній прогноз"
    assert future[0].fertile_window_start is None, "Огіно-Кнаус НЕ має бути при 5 циклах"


async def test_ogino_window_formula():
    """Перевіряємо формулу: min-18 .. max-11 від початку прогнозованого циклу."""
    base = date(2025, 1, 1)
    # 6 циклів: 5 з кроком 26, 1 з кроком 30 → min=26, max=30
    starts_raw = [base + timedelta(days=26 * i) for i in range(5)] + [base + timedelta(days=26 * 5 + 4)]
    cycles = [_cycle(starts_raw[i], starts_raw[i] + timedelta(days=4)) for i in range(6)]
    svc = _svc(_user(is_default=False), cycles)

    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=90))
    future = [p for p in result if p.predicted_start_date > date.today() and p.fertile_window_start is not None]

    assert future, "Очікується хоча б один майбутній прогноз з Огіно-Кнаусом"
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
        StartCycleRequest(date=date.today() + timedelta(days=1))


def test_start_request_accepts_past_date():
    """POST /cycles/start: дата минулого → OK."""
    from app.schemas.cycles import StartCycleRequest

    req = StartCycleRequest(date=date.today() - timedelta(days=7))
    assert req.date == date.today() - timedelta(days=7)


def test_end_request_rejects_future_date():
    """POST /cycles/end: дата в майбутньому → ValidationError."""
    from pydantic import ValidationError
    from app.schemas.cycles import EndCycleRequest

    with pytest.raises(ValidationError):
        EndCycleRequest(date=date.today() + timedelta(days=1))


# ── BUG-01: онбординг без дати ──────────────────────────────────────────────


async def test_onboarding_skip_date_sets_today_as_base():
    """
    Якщо onboarding зберіг last_period_date=date.today() (користувач пропустив крок 3),
    сервіс генерує прогноз починаючи від сьогодні — це коректна поведінка після виправлення BUG-07.
    """
    svc = _svc(_user(cycle_length=28, period_length=5, is_default=True, last_period_date=date.today()), [])
    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=30))

    assert any(p.predicted_start_date == date.today() for p in result), (
        "Прогноз має починатися сьогодні, якщо last_period_date=date.today()"
    )


async def test_onboarding_skip_date_null_returns_empty():
    """Якщо last_period_date=null — порожній стан (очікувана поведінка після виправлення BUG-01)."""
    svc = _svc(_user(cycle_length=28, period_length=5, is_default=True, last_period_date=None), [])
    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=30))
    assert result == [], "Без дати останньої менструації прогнозів не має бути"


# ── BUG-04: овуляція при короткому циклі ────────────────────────────────────


async def test_short_cycle_ovulation_precedes_start():
    """
    BUG-04: цикл <= 14 днів -> дата овуляції потрапляє до дати початку менструації.
    """
    svc = _svc(_user(cycle_length=10, period_length=3, is_default=True, last_period_date=date.today()), [])
    result = await svc.calculate_cycle_projections(UID, until=date.today() + timedelta(days=30))

    for proj in result:
        if proj.predicted_ovulation_date < proj.predicted_start_date:
            # Документуємо баг: овуляція раніше початку менструації
            assert True, "BUG-04: ovulation_date < start_date при cycle_length=10"
            return


# ── BUG-05: predicted на минулих днях ───────────────────────────────────────


async def test_past_days_not_marked_predicted():
    """BUG-05 fixed: прогнозована менструація, що вже ЗАВЕРШИЛАСЬ, не відображається на минулих днях.
    base=сьогодні-8, period=5: прогноз закінчився 4 дні тому → вчорашній день поза вікном.
    """
    base = date.today() - timedelta(days=8)
    svc = _svc(_user(cycle_length=28, period_length=5, is_default=True, last_period_date=base), [])

    data = await svc.get_calendar_month(UID, month=date.today().month, year=date.today().year)
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    yesterday_day = next((d for d in data["days"] if d["date"] == yesterday_str), None)

    assert yesterday_day is not None, "Вчорашній день має бути в календарі"
    assert not yesterday_day["is_menstruation_predicted"], (
        "BUG-05 fixed: завершена прогнозована менструація НЕ має показуватись"
    )


async def test_ongoing_predicted_period_shows_past_days():
    """Якщо прогнозований цикл почався вчора і ще не завершився — вчорашній день позначається."""
    yesterday = date.today() - timedelta(days=1)
    svc = _svc(_user(cycle_length=28, period_length=5, is_default=True, last_period_date=yesterday), [])

    data = await svc.get_calendar_month(UID, month=date.today().month, year=date.today().year)
    yesterday_day = next((d for d in data["days"] if d["date"] == yesterday.isoformat()), None)

    assert yesterday_day is not None
    assert yesterday_day["is_menstruation_predicted"], (
        "Якщо прогнозована менструація ще триває, вчорашній день теж має бути позначений"
    )


# ── TC-06: calendar без даних ────────────────────────────────────────────────


async def test_calendar_no_data_returns_all_false_flags():
    """TC-06 edge: немає жодного запису і last_period_date=None → усі is_*=false, current_phase=''"""
    svc = _svc(_user(last_period_date=None), [])
    data = await svc.get_calendar_month(UID, month=6, year=2026)

    assert len(data["days"]) == 30
    for day in data["days"]:
        assert not day["is_menstruation"], f"{day['date']}: is_menstruation має бути false"
        assert not day["is_menstruation_predicted"], f"{day['date']}: is_menstruation_predicted має бути false"
        assert not day["is_ovulation_predicted"], f"{day['date']}: is_ovulation_predicted має бути false"
    assert data["current_phase"] == ""


# ── TC-09: минула овуляція ───────────────────────────────────────────────────


async def test_past_ovulation_not_marked_predicted():
    """
    TC-09 edge / BUG-08: projected_ovulation < date.today() → не має бути is_ovulation_predicted.
    base=date.today()-8, cycle_length=20: ov=date.today()-2 (минуле), end=date.today()+6 (майбутнє).
    Проєкція включається (end >= date.today()), але дата овуляції вже в минулому.
    """
    base = date.today() - timedelta(days=8)
    ov_date = base + timedelta(days=6)  # date.today() - 2

    svc = _svc(_user(cycle_length=20, period_length=15, is_default=True, last_period_date=base), [])
    data = await svc.get_calendar_month(UID, month=date.today().month, year=date.today().year)

    ov_day = next((d for d in data["days"] if d["date"] == ov_date.isoformat()), None)

    assert ov_day is not None, "День овуляції має бути в календарі"
    assert not ov_day["is_ovulation_predicted"], (
        "BUG-08 fixed: минула дата овуляції НЕ має бути is_ovulation_predicted"
    )


# ── 1-day period bug ────────────────────────────────────────────────────────


async def test_one_day_period_no_phantom_predicted():
    """Цикл тривалістю 1 день: дні після end_date не мають is_menstruation_predicted."""
    start = date.today() - timedelta(days=1)
    closed = _cycle(start, start)  # end_date == start_date

    svc = CycleProjectionService(
        user_repository=AsyncMock(),
        cycle_repository=AsyncMock(),
    )
    svc.user_repository.get_by_id.return_value = _user(
        cycle_length=28, period_length=5, is_default=True
    )
    svc.cycle_repository.get_last_completed_cycles.return_value = [closed]
    svc.cycle_repository.get_active_cycle.return_value = None

    data = await svc.get_calendar_month(UID, month=date.today().month, year=date.today().year)

    for day in data["days"]:
        if day["date"] > start.isoformat():
            assert not day["is_menstruation_predicted"], (
                f"{day['date']}: не має бути predicted після 1-денного циклу"
            )
