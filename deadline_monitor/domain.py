"""Deadline risk assessment. Pure logic: no I/O, no clock access, everything arrives as arguments."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum

from deadline_monitor.workday import end_of_workday, working_minutes_between

# Same pause the planner leaves between consecutive operations.
PAUSE_BETWEEN_OPERATIONS_MINUTES = 5

# Order status number meaning "sent for work order creation": no operations exist yet.
STATUS_AWAITING_WORK_ORDER = 1


class RiskLevel(Enum):
    OVERDUE = "overdue"
    CRITICAL = "critical"
    WARNING = "warning"
    UNPLANNED = "unplanned"


@dataclass(frozen=True)
class PendingOperation:
    work_id: str
    duration_minutes: int


@dataclass(frozen=True)
class OpenOrder:
    id: str
    deadline: date
    status_number: int
    customer_name: str
    operations: tuple[PendingOperation, ...]


@dataclass(frozen=True)
class DeadlineRisk:
    order: OpenOrder
    level: RiskLevel
    required_minutes: int
    available_minutes: int


def required_minutes(order: OpenOrder) -> int:
    """Lower bound of the time still needed to finish the order.

    Operations of one work are sequential, different works can be done by different technicians
    in parallel, so the bound is the longest chain of a single work. If even this does not fit
    before the deadline, the order is late no matter how the lab is staffed.
    """
    chains: dict[str, list[int]] = defaultdict(list)
    for operation in order.operations:
        chains[operation.work_id].append(operation.duration_minutes)
    return max(
        (sum(durations) + PAUSE_BETWEEN_OPERATIONS_MINUTES * (len(durations) - 1) for durations in chains.values()),
        default=0,
    )


def assess(
    order: OpenOrder,
    now: datetime,
    warning_ratio: float,
    planning_horizon_days: int,
) -> DeadlineRisk | None:
    """Return the risk for an order, or None when it is on track."""
    deadline_end = end_of_workday(order.deadline)
    if now >= deadline_end:
        return DeadlineRisk(order, RiskLevel.OVERDUE, required_minutes(order), 0)

    available = working_minutes_between(now, deadline_end)

    if not order.operations:
        days_left = (order.deadline - now.date()).days
        if order.status_number == STATUS_AWAITING_WORK_ORDER and days_left <= planning_horizon_days:
            return DeadlineRisk(order, RiskLevel.UNPLANNED, 0, available)
        return None

    required = required_minutes(order)
    if required > available:
        return DeadlineRisk(order, RiskLevel.CRITICAL, required, available)
    if required > available * warning_ratio:
        return DeadlineRisk(order, RiskLevel.WARNING, required, available)
    return None


_SEVERITY = {RiskLevel.OVERDUE: 0, RiskLevel.CRITICAL: 1, RiskLevel.WARNING: 2, RiskLevel.UNPLANNED: 3}


def find_risks(
    orders: list[OpenOrder],
    now: datetime,
    warning_ratio: float,
    planning_horizon_days: int,
) -> list[DeadlineRisk]:
    risks = [risk for order in orders if (risk := assess(order, now, warning_ratio, planning_horizon_days))]
    return sorted(risks, key=lambda risk: (_SEVERITY[risk.level], risk.order.deadline, risk.order.id))
