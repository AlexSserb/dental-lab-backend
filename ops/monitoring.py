"""
Self-hosted monitoring of the AI workflow: aggregates over the LLM call log and the triage states.

LangSmith gives per-trace dashboards (see README); this module answers the same questions from local data,
so the health report works even when tracing is off or LangSmith is unreachable. `monitoring_digest`
prints it, optionally emails it to EMAIL_ADMIN.
"""
import math
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from defects.models import DefectTriage
from llm.models import LlmCallLog

FAILED_TRIAGE_LIMIT = 5


def percentile(values: list[float], fraction: float) -> float:
    """Nearest-rank percentile (ceil of the 1-based rank); 0 for an empty list."""
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(1, math.ceil(fraction * len(ordered)))
    return ordered[rank - 1]


def llm_stats(hours: int) -> list[dict]:
    """Per feature over the last `hours`: call count, success rate, latency percentiles, tokens, cost."""
    since = timezone.now() - timedelta(hours=hours)
    rows = (
        LlmCallLog.objects.filter(created_at__gte=since)
        .values("feature")
        .annotate(
            total=Count("id"),
            ok=Count("id", filter=Q(success=True)),
            tokens=Sum("prompt_tokens") + Sum("completion_tokens"),
            cost=Sum("cost"),
        )
        .order_by("feature")
    )
    latencies: dict[str, list[float]] = {}
    for row in LlmCallLog.objects.filter(created_at__gte=since).only("feature", "latency"):
        latencies.setdefault(row.feature, []).append(row.latency)

    stats = []
    for row in rows:
        feature_latencies = latencies.get(row["feature"], [])
        stats.append({
            "feature": row["feature"],
            "total": row["total"],
            "ok": row["ok"],
            "failed": row["total"] - row["ok"],
            "success_rate": row["ok"] / row["total"],
            "p50": percentile(feature_latencies, 0.50),
            "p95": percentile(feature_latencies, 0.95),
            "tokens": row["tokens"] or 0,
            "cost": row["cost"] or 0,
        })
    return stats


def triage_health() -> dict:
    """Defect triage states, the oldest open review and the recent failures that need attention."""
    counts = dict(DefectTriage.objects.values_list("state").annotate(total=Count("id")))
    oldest_review = (
        DefectTriage.objects.filter(state=DefectTriage.State.AWAITING_REVIEW)
        .order_by("created_at")
        .values_list("created_at", "id")
        .first()
    )
    failed = list(
        DefectTriage.objects.filter(state=DefectTriage.State.FAILED)
        .order_by("-updated_at")[:FAILED_TRIAGE_LIMIT]
        .values_list("id", "error")
    )
    return {
        "counts": counts,
        "oldest_awaiting_review": oldest_review,
        "failed": failed,
    }
