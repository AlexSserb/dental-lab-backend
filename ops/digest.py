"""Human-readable health report of the AI workflow, in the style of the deadline digest."""
from datetime import datetime

from django.conf import settings
from django.utils import timezone

from defects.models import DefectTriage

STATE_LABELS = dict(DefectTriage.State.choices)


def format_digest(stats: list[dict], health: dict, hours: int, now: datetime) -> tuple[str, str]:
    subject = f"Dental Lab: мониторинг AI за {hours} ч"

    lines = [f"Мониторинг AI-функций за последние {hours} ч на {now:%d.%m.%Y %H:%M}.", ""]

    if stats:
        lines.append("LLM-вызовы (по функциям):")
        for item in stats:
            lines.append(
                f"• {item['feature']}: {item['total']} вызовов, успех {item['success_rate']:.0%}, "
                f"p50 {item['p50']:.1f}с, p95 {item['p95']:.1f}с, токенов {item['tokens']:,}, "
                f"стоимость ${item['cost']:.4f}".replace(",", " ")
            )
    else:
        lines.append("LLM-вызовы: за период вызовов не было.")

    counts = health["counts"]
    if counts:
        lines.append("")
        lines.append("Разборы дефектов:")
        for state, label in STATE_LABELS.items():
            if counts.get(state):
                lines.append(f"• {label}: {counts[state]}")
    else:
        lines.append("")
        lines.append("Разборы дефектов: нет.")

    oldest = health["oldest_awaiting_review"]
    if oldest:
        created_at, triage_id = oldest
        waiting_hours = (timezone.now() - created_at).total_seconds() / 3600
        lines.append("")
        lines.append(f"Разбор дольше всего ждёт решения: {triage_id} ({waiting_hours:.1f} ч).")

    failed = health["failed"]
    if failed:
        lines.append("")
        lines.append("Последние ошибки обработки:")
        for triage_id, error in failed:
            lines.append(f"• {triage_id}: {error[:120]}")

    lines.append("")
    lines.append(f"Подробные трейсы: https://smith.langchain.com (проект {settings.LANGSMITH_PROJECT}),")
    lines.append("оповещения LangSmith приходят на вебхук /api/ops/alerts/.")
    return subject, "\n".join(lines)
