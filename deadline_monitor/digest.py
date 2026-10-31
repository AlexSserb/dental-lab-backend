"""Human-readable summary of deadline risks."""

from datetime import datetime

from deadline_monitor.domain import DeadlineRisk, RiskLevel

MAX_LISTED_ORDERS = 50

_LABELS = {
    RiskLevel.OVERDUE: "Срок истёк",
    RiskLevel.CRITICAL: "Не успеваем",
    RiskLevel.WARNING: "Мало запаса",
    RiskLevel.UNPLANNED: "Наряд не сформирован",
}


def format_digest(risks: list[DeadlineRisk], now: datetime) -> tuple[str, str]:
    subject = f"Dental Lab: {len(risks)} order(s) at risk of missing the deadline"

    lines = [f"Контроль сроков на {now:%d.%m.%Y %H:%M} UTC. Заказов под угрозой: {len(risks)}.", ""]
    for risk in risks[:MAX_LISTED_ORDERS]:
        order = risk.order
        line = f"• {order.id[:8]} | {order.customer_name or 'без заказчика'} | срок {order.deadline:%d.%m.%Y} | "
        line += _LABELS[risk.level]
        if risk.level in (RiskLevel.CRITICAL, RiskLevel.WARNING):
            line += f": нужно {_hours(risk.required_minutes)} ч, доступно {_hours(risk.available_minutes)} ч"
        lines.append(line)
    if len(risks) > MAX_LISTED_ORDERS:
        lines.append(f"…и ещё {len(risks) - MAX_LISTED_ORDERS}")
    return subject, "\n".join(lines)


def _hours(minutes: int) -> str:
    return f"{minutes / 60:.1f}"
