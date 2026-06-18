import uuid
from datetime import date
from types import SimpleNamespace

import pytest

from app.controllers import cycles_controller
from app.schemas.cycles import EndCycleRequest, StartCycleRequest


UID = uuid.uuid4()


def _cycle(start, end=None):
    return SimpleNamespace(id=uuid.uuid4(), user_id=UID, start_date=start, end_date=end)


class _State:
    def __init__(self, cycles):
        self.cycles = cycles
        self.user = SimpleNamespace(average_period_length=5)
        self.user_updates = []


class _FakeCycleRepository:
    def __init__(self, state):
        self.state = state

    async def get_active_cycle(self, user_id):
        return next((c for c in self.state.cycles if c.user_id == user_id and c.end_date is None), None)

    async def get_next_cycle(self, user_id, after_date):
        cycles = sorted(
            (c for c in self.state.cycles if c.user_id == user_id and c.start_date > after_date),
            key=lambda c: c.start_date,
        )
        return cycles[0] if cycles else None

    async def get_cycle_containing_date(self, user_id, target_date):
        cycles = sorted(
            (
                c for c in self.state.cycles
                if c.user_id == user_id
                and c.start_date <= target_date
                and (c.end_date is None or c.end_date >= target_date)
            ),
            key=lambda c: c.start_date,
            reverse=True,
        )
        return cycles[0] if cycles else None

    async def create_cycle(self, user_id, start_date):
        cycle = _cycle(start_date)
        self.state.cycles.append(cycle)
        return cycle

    async def close_cycle(self, cycle, end_date):
        cycle.end_date = end_date
        return cycle

    async def create_closed_cycle(self, user_id, start_date, end_date):
        cycle = _cycle(start_date, end_date)
        self.state.cycles.append(cycle)
        return cycle

    async def close_and_create_cycle(self, old_cycle, close_date, user_id, start_date):
        old_cycle.end_date = close_date
        return await self.create_cycle(user_id, start_date)

    async def update_start(self, cycle, start_date):
        cycle.start_date = start_date
        return cycle

    async def get_last_completed_cycles(self, user_id, limit=10):
        return [
            c for c in sorted(self.state.cycles, key=lambda c: c.start_date, reverse=True)
            if c.user_id == user_id and c.end_date is not None
        ][:limit]

    async def get_by_id(self, cycle_id, user_id):
        return next((c for c in self.state.cycles if c.id == cycle_id and c.user_id == user_id), None)


class _FakeUserRepository:
    def __init__(self, state):
        self.state = state

    async def get_by_id(self, user_id):
        return self.state.user

    async def update_fields(self, user_id, values):
        self.state.user_updates.append(values)
        return self.state.user


@pytest.fixture(autouse=True)
def fake_repositories(monkeypatch):
    monkeypatch.setattr(cycles_controller, "CycleRepository", _FakeCycleRepository)
    monkeypatch.setattr(cycles_controller, "UserRepository", _FakeUserRepository)


async def test_start_before_existing_cycle_creates_closed_historical_cycle():
    state = _State([_cycle(date(2026, 6, 16), date(2026, 6, 20))])

    response = await cycles_controller.start_cycle(
        StartCycleRequest(date=date(2026, 5, 20)),
        user_id=UID,
        session=state,
    )

    assert response.start_date == date(2026, 5, 20)
    assert response.end_date == date(2026, 5, 24)
    assert all(c.end_date is not None for c in state.cycles)
    assert state.user_updates == []


async def test_historical_cycle_is_bounded_by_next_recorded_cycle():
    state = _State([_cycle(date(2026, 5, 23), date(2026, 5, 27)), _cycle(date(2026, 6, 16))])

    response = await cycles_controller.start_cycle(
        StartCycleRequest(date=date(2026, 5, 20)),
        user_id=UID,
        session=state,
    )

    assert response.start_date == date(2026, 5, 20)
    assert response.end_date == date(2026, 5, 22)


async def test_start_at_next_cycle_start_returns_existing_cycle():
    active = _cycle(date(2026, 5, 20))
    current = _cycle(date(2026, 6, 16), date(2026, 6, 20))
    state = _State([active, current])

    response = await cycles_controller.start_cycle(
        StartCycleRequest(date=date(2026, 6, 16)),
        user_id=UID,
        session=state,
    )

    assert response.id == str(current.id)
    assert response.start_date == current.start_date
    assert len(state.cycles) == 2


async def test_updating_cycle_end_cannot_overlap_next_cycle():
    first = _cycle(date(2026, 5, 20), date(2026, 5, 24))
    state = _State([first, _cycle(date(2026, 5, 25), date(2026, 5, 29))])

    with pytest.raises(cycles_controller.HTTPException):
        await cycles_controller.update_cycle_end(
            first.id,
            EndCycleRequest(date=date(2026, 5, 25)),
            user_id=UID,
            session=state,
        )
