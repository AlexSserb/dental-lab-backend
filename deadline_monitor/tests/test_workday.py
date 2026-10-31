from datetime import datetime, timezone
from unittest import TestCase

from deadline_monitor.workday import working_minutes_between


def utc(day: int, hour: int, minute: int = 0) -> datetime:
    # November 2026: the 2nd is a Monday, the 7th a Saturday
    return datetime(2026, 11, day, hour, minute, tzinfo=timezone.utc)


class WorkingMinutesTest(TestCase):
    def test_full_working_day(self):
        self.assertEqual(working_minutes_between(utc(2, 0), utc(2, 23)), 480)

    def test_lunch_break_is_not_counted(self):
        self.assertEqual(working_minutes_between(utc(2, 7), utc(2, 10)), 120)

    def test_partial_day(self):
        self.assertEqual(working_minutes_between(utc(2, 10), utc(2, 13)), 180)

    def test_weekend_is_skipped(self):
        self.assertEqual(working_minutes_between(utc(6, 12), utc(9, 5)), 120)

    def test_only_weekend(self):
        self.assertEqual(working_minutes_between(utc(7, 0), utc(8, 23)), 0)

    def test_end_before_start(self):
        self.assertEqual(working_minutes_between(utc(3, 10), utc(2, 10)), 0)
