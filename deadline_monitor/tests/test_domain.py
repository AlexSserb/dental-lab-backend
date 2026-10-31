from datetime import date, datetime, timezone
from unittest import TestCase

from deadline_monitor.domain import (
    OpenOrder,
    PendingOperation,
    RiskLevel,
    assess,
    find_risks,
    required_minutes,
)

NOW = datetime(2026, 11, 2, 4, 0, tzinfo=timezone.utc)  # Monday, start of the working day


def make_order(deadline: date, operations=(), status_number: int = 3, order_id: str = "order-1") -> OpenOrder:
    return OpenOrder(order_id, deadline, status_number, "Клиника", tuple(operations))


def chain(work_id: str, *durations: int) -> list[PendingOperation]:
    return [PendingOperation(work_id, duration) for duration in durations]


class RequiredMinutesTest(TestCase):
    def test_operations_of_one_work_are_sequential_with_pauses(self):
        order = make_order(date(2026, 11, 3), chain("w1", 60, 30, 30))
        self.assertEqual(required_minutes(order), 120 + 2 * 5)

    def test_different_works_run_in_parallel(self):
        order = make_order(date(2026, 11, 3), chain("w1", 60) + chain("w2", 200))
        self.assertEqual(required_minutes(order), 200)

    def test_no_operations(self):
        self.assertEqual(required_minutes(make_order(date(2026, 11, 3))), 0)


class AssessTest(TestCase):
    def assess(self, order):
        return assess(order, NOW, warning_ratio=0.8, planning_horizon_days=3)

    def test_deadline_passed(self):
        risk = self.assess(make_order(date(2026, 11, 1), chain("w1", 10)))
        self.assertEqual(risk.level, RiskLevel.OVERDUE)

    def test_deadline_day_after_workday_end_is_overdue(self):
        late = datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc)
        risk = assess(make_order(date(2026, 11, 2), chain("w1", 10)), late, 0.8, 3)
        self.assertEqual(risk.level, RiskLevel.OVERDUE)

    def test_critical_when_work_does_not_fit(self):
        risk = self.assess(make_order(date(2026, 11, 2), chain("w1", 300, 300)))  # 8 h available today
        self.assertEqual(risk.level, RiskLevel.CRITICAL)
        self.assertEqual((risk.required_minutes, risk.available_minutes), (605, 480))

    def test_warning_when_little_slack(self):
        risk = self.assess(make_order(date(2026, 11, 2), chain("w1", 400)))  # 400 of 480 > 80 %
        self.assertEqual(risk.level, RiskLevel.WARNING)

    def test_on_track(self):
        self.assertIsNone(self.assess(make_order(date(2026, 11, 2), chain("w1", 100))))

    def test_weekend_before_deadline_reduces_capacity(self):
        friday_noon = datetime(2026, 11, 6, 10, 0, tzinfo=timezone.utc)
        order = make_order(date(2026, 11, 9), chain("w1", 400))  # only 180 min Friday + 480 Monday
        self.assertIsNone(assess(order, friday_noon, 0.8, 3))
        tight = make_order(date(2026, 11, 7), chain("w1", 200))  # deadline Saturday: 180 min left
        self.assertEqual(assess(tight, friday_noon, 0.8, 3).level, RiskLevel.CRITICAL)

    def test_unplanned_order_near_deadline(self):
        risk = self.assess(make_order(date(2026, 11, 4), status_number=1))
        self.assertEqual(risk.level, RiskLevel.UNPLANNED)

    def test_unplanned_order_far_from_deadline(self):
        self.assertIsNone(self.assess(make_order(date(2026, 12, 1), status_number=1)))

    def test_in_work_order_without_pending_operations_is_fine(self):
        self.assertIsNone(self.assess(make_order(date(2026, 11, 3), status_number=3)))


class FindRisksTest(TestCase):
    def test_most_severe_first(self):
        warning = make_order(date(2026, 11, 2), chain("w1", 400), order_id="a")
        overdue = make_order(date(2026, 10, 30), chain("w1", 10), order_id="b")
        fine = make_order(date(2026, 11, 20), chain("w1", 10), order_id="c")

        risks = find_risks([warning, overdue, fine], NOW, 0.8, 3)

        self.assertEqual([risk.order.id for risk in risks], ["b", "a"])
