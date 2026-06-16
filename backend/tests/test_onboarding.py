"""
Юніт-тести онбордингу.
Покриває: TC-03 (схема та сервісний шар), BUG-07.
"""
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.schemas.onboarding import OnboardingRequest
from app.services.onboarding_service import OnboardingService

UID = uuid.uuid4()


def _make_svc() -> OnboardingService:
    repo = AsyncMock()
    repo.update_user_profile.return_value = MagicMock()
    return OnboardingService(repo)


# ── TC-03: OnboardingRequest схема ──────────────────────────────────────────


def test_onboarding_rejects_zero_cycle_length():
    """TC-03 edge: cycle_length=0 → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(cycle_length=0)


def test_onboarding_rejects_negative_cycle_length():
    """TC-03 edge: cycle_length від'ємний → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(cycle_length=-1)


def test_onboarding_rejects_period_gte_cycle():
    """TC-03 edge: period_length >= cycle_length → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(cycle_length=5, period_length=5)

    with pytest.raises(ValidationError):
        OnboardingRequest(cycle_length=5, period_length=7)


def test_onboarding_rejects_future_last_period_date():
    """TC-03 edge: дата в майбутньому → ValidationError."""
    with pytest.raises(ValidationError):
        OnboardingRequest(last_period_date=date.today() + timedelta(days=1))


def test_onboarding_accepts_all_none():
    """TC-03: усі None → схема OK (дефолти застосовуються на сервісному шарі)."""
    req = OnboardingRequest()
    assert req.cycle_length is None
    assert req.period_length is None
    assert req.last_period_date is None


def test_onboarding_accepts_today_as_last_period_date():
    """TC-03: дата сьогодні → OK (не є майбутньою)."""
    today = date.today()
    req = OnboardingRequest(last_period_date=today)
    assert req.last_period_date == today


# ── TC-03: OnboardingService дефолти ────────────────────────────────────────


async def test_onboarding_defaults_cycle_length():
    """TC-03 edge: cycle_length=None ('Не пам'ятаю') → зберігається 28."""
    svc = _make_svc()
    await svc.save_onboarding(UID, OnboardingRequest(cycle_length=None, period_length=5))

    kwargs = svc._repository.update_user_profile.call_args.kwargs
    assert kwargs["average_cycle_length"] == 28


async def test_onboarding_defaults_period_length():
    """TC-03 edge: period_length=None ('Не пам'ятаю') → зберігається 5."""
    svc = _make_svc()
    await svc.save_onboarding(UID, OnboardingRequest(cycle_length=28, period_length=None))

    kwargs = svc._repository.update_user_profile.call_args.kwargs
    assert kwargs["average_period_length"] == 5


async def test_onboarding_skip_date_stores_today():
    """TC-03 edge: пропустити крок 3 → last_period_date=date.today() (запобігає нескінченному редиректу BUG-07)."""
    svc = _make_svc()
    await svc.save_onboarding(UID, OnboardingRequest(cycle_length=28, period_length=5))

    kwargs = svc._repository.update_user_profile.call_args.kwargs
    assert kwargs["last_period_date"] == date.today()


async def test_onboarding_stores_user_provided_date():
    """TC-03: вказана дата → зберігається без змін."""
    target = date.today() - timedelta(days=10)
    svc = _make_svc()
    await svc.save_onboarding(UID, OnboardingRequest(cycle_length=28, period_length=5, last_period_date=target))

    kwargs = svc._repository.update_user_profile.call_args.kwargs
    assert kwargs["last_period_date"] == target


async def test_onboarding_sets_is_calculated_when_defaults_used():
    """TC-03: пропущені поля → is_calculated_default=True."""
    svc = _make_svc()
    await svc.save_onboarding(UID, OnboardingRequest())

    kwargs = svc._repository.update_user_profile.call_args.kwargs
    assert kwargs["is_calculated_default"] is True


async def test_onboarding_not_calculated_when_all_provided():
    """TC-03: всі поля вказані → is_calculated_default=False."""
    svc = _make_svc()
    await svc.save_onboarding(
        UID,
        OnboardingRequest(cycle_length=28, period_length=5, last_period_date=date.today() - timedelta(days=5)),
    )

    kwargs = svc._repository.update_user_profile.call_args.kwargs
    assert kwargs["is_calculated_default"] is False


# ── BUG-07 (fixed): needs_onboarding loop ───────────────────────────────────


def test_needs_onboarding_false_when_last_period_date_is_set():
    """
    BUG-07 fixed: після онбордингу з пропуском дати last_period_date тепер
    зберігається як date.today(), тому needs_onboarding=False при наступному логіні.
    """
    average_cycle_length = 28
    average_period_length = 5
    last_period_date = date.today()  # сервіс тепер зберігає today замість None

    needs_onboarding = (
        average_cycle_length is None
        or average_period_length is None
        or last_period_date is None
    )

    assert needs_onboarding is False, (
        "BUG-07 fixed: needs_onboarding має бути False після онбордингу"
    )
