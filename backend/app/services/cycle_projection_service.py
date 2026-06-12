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
    fertile_window_start: date | None = None
    fertile_window_end: date | None = None


class CycleProjectionService:
    def __init__(self, user_repository: UserRepository, cycle_repository: CycleRepository):
        self.user_repository = user_repository
        self.cycle_repository = cycle_repository

    async def calculate_cycle_projections(
        self, user_id: uuid.UUID, until: date, active_start: date | None = None
    ) -> list[CycleProjection]:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return []

        completed_cycles = await self.cycle_repository.get_last_completed_cycles(user_id)

        # База прогнозування: активний цикл має пріоритет над завершеними
        if active_start is not None:
            base_date = active_start
        elif completed_cycles:
            base_date = completed_cycles[0].start_date
        elif user.last_period_date:
            base_date = user.last_period_date
        else:
            return []

        # Тривалість циклу та вікно Огіно-Кнауса
        use_ogino = False
        min_cycle = max_cycle = 0

        if user.is_calculated_default or len(completed_cycles) < 3:
            cycle_length = user.average_cycle_length or 28
        else:
            sorted_cycles = sorted(completed_cycles, key=lambda c: c.start_date)
            diffs = [
                (sorted_cycles[i + 1].start_date - sorted_cycles[i].start_date).days
                for i in range(len(sorted_cycles) - 1)
            ]
            cycle_length = round(sum(diffs) / len(diffs))
            if len(diffs) >= 5:
                use_ogino = True
                min_cycle = min(diffs)
                max_cycle = max(diffs)

        period_length = user.average_period_length or 5
        today = date.today()

        projections = []
        days_since_base = max(0, (today - base_date).days)
        start_multiplier = max(0, (days_since_base - cycle_length) // cycle_length)

        multiplier = start_multiplier
        while True:
            predicted_start = base_date + timedelta(days=cycle_length * multiplier)
            if predicted_start > until:
                break
            predicted_end = predicted_start + timedelta(days=period_length - 1)
            predicted_ovulation = predicted_start + timedelta(days=cycle_length - 14)

            fertile_window_start = None
            fertile_window_end = None
            if use_ogino:
                fertile_window_start = predicted_start + timedelta(days=min_cycle - 18)
                fertile_window_end = predicted_start + timedelta(days=max_cycle - 11)

            if predicted_end >= today or predicted_ovulation >= today:
                projections.append(CycleProjection(
                    predicted_start_date=predicted_start,
                    predicted_end_date=predicted_end,
                    predicted_ovulation_date=predicted_ovulation,
                    fertile_window_start=fertile_window_start,
                    fertile_window_end=fertile_window_end,
                ))
            multiplier += 1

        return projections

    @staticmethod
    def _days_word(n: int) -> str:
        mod100, mod10 = n % 100, n % 10
        if 11 <= mod100 <= 19:
            return "днів"
        if mod10 == 1:
            return "день"
        if 2 <= mod10 <= 4:
            return "дні"
        return "днів"

    def _determine_current_phase(
        self, active_cycle, projections: list[CycleProjection], period_length: int = 5
    ) -> tuple[str, str]:
        today = date.today()
        w = self._days_word

        if active_cycle:
            day_n = (today - active_cycle.start_date).days + 1
            expected_end = active_cycle.start_date + timedelta(days=period_length - 1)
            if today <= expected_end:
                days_left = (expected_end - today).days
                return "Менструальна фаза", f"День {day_n} — ще {days_left} {w(days_left)} до завершення"
            # Цикл ще відкритий, але менструація вже за розкладом завершилась
            if projections:
                days_until_ov = (projections[0].predicted_ovulation_date - today).days
                if days_until_ov > 1:
                    return "Фолікулярна фаза", f"До овуляції {days_until_ov} {w(days_until_ov)} — рівень енергії зростає"
                if days_until_ov >= -1:
                    return "Овуляція", "Найвища ймовірність завагітніти"
                next_start = next((p.predicted_start_date for p in projections if p.predicted_start_date > today), None)
                if next_start:
                    d = (next_start - today).days
                    return "Лютеальна фаза", f"До менструації {d} {w(d)} — слухай своє тіло"
            return "Фолікулярна фаза", "Організм готується до овуляції"

        if not projections:
            return "", ""

        next_proj = projections[0]
        ov_diff = (next_proj.predicted_ovulation_date - today).days

        if ov_diff == 0:
            return "Овуляція", "Сьогодні найвища ймовірність завагітніти"
        if ov_diff == 1:
            return "Овуляція", "Завтра очікується овуляція — фертильний пік"
        if ov_diff == -1:
            return "Овуляція", "Вчора була овуляція — ще є шанс завагітніти"

        if next_proj.predicted_start_date <= today <= next_proj.predicted_end_date:
            day_n = (today - next_proj.predicted_start_date).days + 1
            days_left = (next_proj.predicted_end_date - today).days
            return "Менструальна фаза", f"День {day_n} — ще {days_left} {w(days_left)} до завершення"

        if next_proj.predicted_end_date < today < next_proj.predicted_ovulation_date:
            days_until_ov = (next_proj.predicted_ovulation_date - today).days
            return "Фолікулярна фаза", f"До овуляції {days_until_ov} {w(days_until_ov)} — рівень енергії зростає"

        if today > next_proj.predicted_ovulation_date:
            next_start = next((p.predicted_start_date for p in projections if p.predicted_start_date > today), None)
            if next_start:
                days_until = (next_start - today).days
                return "Лютеальна фаза", f"До менструації {days_until} {w(days_until)} — слухай своє тіло"
            return "Лютеальна фаза", "Організм готується до наступного циклу"

        return "", ""

    async def get_calendar_month(self, user_id: uuid.UUID, month: int, year: int) -> dict:
        last_day = monthrange(year, month)[1]
        until = date(year, month, last_day)

        active_cycle = await self.cycle_repository.get_active_cycle(user_id)
        projections = await self.calculate_cycle_projections(
            user_id, until,
            active_start=active_cycle.start_date if active_cycle else None,
        )
        recent = await self.cycle_repository.get_last_completed_cycles(user_id, limit=1)
        last_completed = recent[0] if recent else None
        user = await self.user_repository.get_by_id(user_id)
        period_length = (user.average_period_length if user else None) or 5
        today = date.today()

        days = []
        for day in range(1, last_day + 1):
            current_date = date(year, month, day)

            is_menstruation = False
            if active_cycle and active_cycle.end_date is None:
                # Весь очікуваний період одразу реальна менструація
                expected_end = active_cycle.start_date + timedelta(days=period_length - 1)
                is_menstruation = active_cycle.start_date <= current_date <= expected_end
            elif active_cycle and active_cycle.end_date:
                is_menstruation = active_cycle.start_date <= current_date <= active_cycle.end_date
            elif last_completed:
                is_menstruation = last_completed.start_date <= current_date <= last_completed.end_date

            is_menstruation_predicted = False
            is_ovulation_predicted = False
            is_fertile_window = False

            for proj in projections:
                # Якщо цикл вже закрито — беремо реальну дату кінця, а не прогнозовану
                proj_end = proj.predicted_end_date
                if (last_completed and last_completed.end_date
                        and proj.predicted_start_date == last_completed.start_date):
                    proj_end = last_completed.end_date

                if proj.predicted_start_date <= current_date <= proj_end:
                    is_menstruation_predicted = True
                if current_date == proj.predicted_ovulation_date:
                    is_ovulation_predicted = True
                if (proj.fertile_window_start and proj.fertile_window_end
                        and proj.fertile_window_start <= current_date <= proj.fertile_window_end
                        and not is_menstruation):
                    is_fertile_window = True

            # Пріоритет реальної менструації над прогнозом
            if is_menstruation:
                is_menstruation_predicted = False
                is_fertile_window = False

            days.append({
                "date": current_date.isoformat(),
                "is_menstruation": is_menstruation,
                "is_menstruation_predicted": is_menstruation_predicted,
                "is_ovulation_predicted": is_ovulation_predicted,
                "is_fertile_window": is_fertile_window,
            })

        current_phase, phase_subtitle = self._determine_current_phase(active_cycle, projections, period_length)

        return {
            "days": days,
            "current_phase": current_phase,
            "phase_subtitle": phase_subtitle,
            "active_cycle": {
                "id": str(active_cycle.id),
                "start_date": active_cycle.start_date.isoformat(),
            } if active_cycle else None,
        }
