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
        cycle_length, period_length, use_ogino, min_cycle, max_cycle = self._compute_cycle_params(
            user, completed_cycles
        )
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
    def _compute_cycle_params(
        user, completed_cycles: list
    ) -> tuple[int, int, bool, int, int]:
        """Повертає (cycle_length, period_length, use_ogino, min_cycle, max_cycle)."""
        use_ogino = False
        min_cycle = max_cycle = 0
        if user.is_calculated_default or len(completed_cycles) < 3:
            cycle_length = user.average_cycle_length or 28
        else:
            sorted_c = sorted(completed_cycles, key=lambda c: c.start_date)
            diffs = [
                (sorted_c[i + 1].start_date - sorted_c[i].start_date).days
                for i in range(len(sorted_c) - 1)
            ]
            cycle_length = round(sum(diffs) / len(diffs))
            if len(diffs) >= 5:
                use_ogino = True
                min_cycle = min(diffs)
                max_cycle = max(diffs)
        period_length = user.average_period_length or 5
        return cycle_length, period_length, use_ogino, min_cycle, max_cycle

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
                if days_left == 0:
                    return "Менструальна фаза", f"День {day_n} — останній день"
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
            if days_left == 0:
                return "Менструальна фаза", f"День {day_n} — останній день"
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

        month_start = date(year, month, 1)
        active_cycle = await self.cycle_repository.get_active_cycle(user_id)
        projections = await self.calculate_cycle_projections(
            user_id, until,
            active_start=active_cycle.start_date if active_cycle else None,
        )
        recent = await self.cycle_repository.get_last_completed_cycles(user_id, limit=24)
        # Завершені цикли, що перетинаються з запитуваним місяцем
        completed_in_month = [
            c for c in recent
            if c.end_date and c.start_date <= until and c.end_date >= month_start
        ]
        last_completed = recent[0] if recent else None
        user = await self.user_repository.get_by_id(user_id)
        cycle_length, period_length, _, _, _ = (
            self._compute_cycle_params(user, recent) if user else (28, 5, False, 0, 0)
        )
        today = date.today()

        # Стартові дати завершених циклів — проекції, що збігаються з ними, є історичними, а не прогнозом
        known_cycle_starts = {c.start_date for c in recent}

        # Ов'уляції для проміжків між завершеними циклами (для відображення фаз між ними)
        sorted_recent = sorted(recent, key=lambda c: c.start_date)
        cycle_next_starts: dict = {}
        for i, c in enumerate(sorted_recent):
            if i + 1 < len(sorted_recent):
                cycle_next_starts[c.id] = sorted_recent[i + 1].start_date
            elif active_cycle:
                cycle_next_starts[c.id] = active_cycle.start_date
        hist_ov_dates: set[date] = set()
        for c in recent:
            if not c.end_date:
                continue
            hist_ov = c.start_date + timedelta(days=cycle_length - 14)
            next_s = cycle_next_starts.get(c.id)
            if hist_ov <= c.end_date:  # ов'уляція всередині менструації — пропускаємо
                continue
            if next_s and hist_ov >= next_s:  # виходить за межі наступного циклу
                continue
            hist_ov_dates.add(hist_ov)

        days = []
        for day in range(1, last_day + 1):
            current_date = date(year, month, day)

            is_menstruation = False
            # Активний (відкритий) цикл — очікуваний кінець як реальна менструація
            if active_cycle and active_cycle.end_date is None:
                expected_end = active_cycle.start_date + timedelta(days=period_length - 1)
                if active_cycle.start_date <= current_date <= expected_end:
                    is_menstruation = True
            # Завершені цикли цього місяця — реальна менструація з БД
            if not is_menstruation:
                for c in completed_in_month:
                    if c.start_date <= current_date <= c.end_date:
                        is_menstruation = True
                        break

            is_menstruation_predicted = False
            is_ovulation_predicted = False
            is_fertile_window = False

            for proj in projections:
                # Пропускаємо проекцію, якщо вона відповідає відомому завершеному циклу
                if proj.predicted_start_date in known_cycle_starts:
                    continue

                if proj.predicted_start_date <= current_date <= proj.predicted_end_date:
                    is_menstruation_predicted = True
                if current_date == proj.predicted_ovulation_date:
                    is_ovulation_predicted = True
                if (proj.fertile_window_start and proj.fertile_window_end
                        and proj.fertile_window_start <= current_date <= proj.fertile_window_end
                        and not is_menstruation):
                    is_fertile_window = True

            # Ов'уляція між завершеними циклами (для відображення фаз у проміжках)
            if not is_menstruation and not is_ovulation_predicted and current_date in hist_ov_dates:
                is_ovulation_predicted = True

            # Пріоритет реальної менструації над прогнозом
            if is_menstruation:
                is_menstruation_predicted = False
                is_fertile_window = False
                is_ovulation_predicted = False

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
            "completed_cycles": [
                {
                    "id": str(c.id),
                    "start_date": c.start_date.isoformat(),
                    "end_date": c.end_date.isoformat() if c.end_date else None,
                }
                for c in recent
            ],
        }
