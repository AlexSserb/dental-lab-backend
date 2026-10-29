"""Lab working calendar.

Mirrors the schedule used by OperationService._adjust_to_work_hours: 04:00-08:00 and 09:00-13:00 UTC,
Monday to Friday. Kept as pure functions so the arithmetic is easy to test.
"""

from datetime import date, datetime, time, timedelta, timezone

WORKING_INTERVALS = ((time(4, 0), time(8, 0)), (time(9, 0), time(13, 0)))
WORKING_WEEKDAYS = frozenset(range(5))


def end_of_workday(day: date) -> datetime:
    return datetime.combine(day, WORKING_INTERVALS[-1][1], tzinfo=timezone.utc)


def working_minutes_between(start: datetime, end: datetime) -> int:
    """Whole working minutes inside [start, end]; both must be timezone-aware."""
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    if end <= start:
        return 0

    total = timedelta()
    day = start.date()
    while day <= end.date():
        if day.weekday() in WORKING_WEEKDAYS:
            for opens, closes in WORKING_INTERVALS:
                lower = max(start, datetime.combine(day, opens, tzinfo=timezone.utc))
                upper = min(end, datetime.combine(day, closes, tzinfo=timezone.utc))
                if upper > lower:
                    total += upper - lower
        day += timedelta(days=1)
    return int(total.total_seconds() // 60)
