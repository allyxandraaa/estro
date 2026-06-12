import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from calendar import monthrange

from app.repositories.user_repository import UserRepository
from app.repositories.cycle_repository import CycleRepository


@dataclass
class CycleProjection:
    predicted_start_date: date
    predicted_end_date: date
    predicted_ovulation_date: date


class CycleProjectionService:
    def __init__(self, user_repository: UserRepository, cycle_repository: CycleRepository):
        self.user_repository = user_repository
        self.cycle_repository = cycle_repository

    async def calculate_cycle_projections(
        self, user_id: uuid.UUID, until: date
    ) -> list[CycleProjection]:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return []

        completed_cycles = await self.cycle_repository.get_last_completed_cycles(user_id)

        # База прогнозування
        if completed_cycles:
            base_date = completed_cycles[0].start_date
        elif user.last_period_date:
            base_date = user.last_period_date
        else:
            return []

        # Тривалість циклу
        if user.is_calculated_default or len(completed_cycles) < 3:
            cycle_length = user.average_cycle_length or 28
        else:
            sorted_cycles = sorted(completed_cycles, key=lambda c: c.start_date)
            diffs = [
                (sorted_cycles[i + 1].start_date - sorted_cycles[i].start_date).days
                for i in range(len(sorted_cycles) - 1)
            ]
            cycle_length = round(sum(diffs) / len(diffs))

        period_length = user.average_period_length or 5
        today = date.today()

        projections = []
        multiplier = 1
        while True:
            predicted_start = base_date + timedelta(days=cycle_length * multiplier)
            if predicted_start > until:
                break
            if predicted_start >= today:
                predicted_end = predicted_start + timedelta(days=period_length - 1)
                predicted_ovulation = predicted_start + timedelta(days=cycle_length - 14)
                projections.append(CycleProjection(
                    predicted_start_date=predicted_start,
                    predicted_end_date=predicted_end,
                    predicted_ovulation_date=predicted_ovulation,
                ))
            multiplier += 1

        return projections

    def _determine_current_phase(self, active_cycle, projections: list[CycleProjection]) -> tuple[str, str]:
        today = date.today()

        if active_cycle:
            return "Менструальна фаза", "Ти зараз в менструальній фазі"

        if not projections:
            return "", ""

        next_proj = projections[0]

        if abs((today - next_proj.predicted_ovulation_date).days) <= 1:
            return "Овуляція", "Сьогодні найвища ймовірність завагітніти"

        if next_proj.predicted_start_date <= today <= next_proj.predicted_end_date:
            return "Менструальна фаза", "Ти зараз в менструальній фазі"

        if next_proj.predicted_end_date < today < next_proj.predicted_ovulation_date:
            return "Фолікулярна фаза", "Організм готується до овуляції"

        if today > next_proj.predicted_ovulation_date:
            return "Лютеальна фаза", "Організм готується до наступного циклу"

        return "", ""

    async def get_calendar_month(self, user_id: uuid.UUID, month: int, year: int) -> dict:
        last_day = monthrange(year, month)[1]
        until = date(year, month, last_day)

        projections = await self.calculate_cycle_projections(user_id, until)
        active_cycle = await self.cycle_repository.get_active_cycle(user_id)
        today = date.today()

        days = []
        for day in range(1, last_day + 1):
            current_date = date(year, month, day)

            is_menstruation = False
            if active_cycle and active_cycle.end_date is None:
                is_menstruation = active_cycle.start_date <= current_date <= today
            elif active_cycle and active_cycle.end_date:
                is_menstruation = active_cycle.start_date <= current_date <= active_cycle.end_date

            is_menstruation_predicted = False
            is_ovulation_predicted = False

            for proj in projections:
                if proj.predicted_start_date <= current_date <= proj.predicted_end_date:
                    is_menstruation_predicted = True
                if current_date == proj.predicted_ovulation_date:
                    is_ovulation_predicted = True

            # Пріоритет реальної менструації над прогнозом
            if is_menstruation:
                is_menstruation_predicted = False

            days.append({
                "date": current_date.isoformat(),
                "is_menstruation": is_menstruation,
                "is_menstruation_predicted": is_menstruation_predicted,
                "is_ovulation_predicted": is_ovulation_predicted,
            })

        current_phase, phase_subtitle = self._determine_current_phase(active_cycle, projections)

        return {
            "days": days,
            "current_phase": current_phase,
            "phase_subtitle": phase_subtitle,
            "active_cycle": {
                "id": str(active_cycle.id),
                "start_date": active_cycle.start_date.isoformat(),
            } if active_cycle else None,
        }
