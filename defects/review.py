"""
The decision service shared by the admin API and the Django admin review page.

Both surfaces validate the administrator's answer the same way and write it the same way; the worker then
resumes the paused graph. Similar-case lookup lives here too: the review UI shows the same precedents as the
detail endpoint.
"""
import logging

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from defects.models import DefectTriage
from defects.serializers import TriageDecisionSerializer

logger = logging.getLogger(__name__)


class DecisionRejected(Exception):
    """The decision was not stored: `status` is the HTTP-worthy code, `errors` the explanation for the UI."""

    def __init__(self, status: int, detail: str = "", errors: dict | None = None):
        super().__init__(detail or str(errors))
        self.status = status
        self.detail = detail
        self.errors = errors or {}


def decide(triage_id: str, user, payload: dict) -> DefectTriage:
    """
    Validate `payload` (action/note/final) against the triage and store the decision. Raises DecisionRejected
    with a 409 for a double decision or a wrong state, and with a 400 for an invalid payload.
    """
    triage = DefectTriage.objects.get(id=triage_id)
    if triage.state != DefectTriage.State.AWAITING_REVIEW:
        raise DecisionRejected(
            409, detail=f"Разбор не ждёт решения (состояние: {triage.get_state_display()}).",
        )

    serializer = TriageDecisionSerializer(data=payload, context={"triage": triage})
    if not serializer.is_valid():
        raise DecisionRejected(400, errors=serializer.errors)

    # Re-checked under a lock: two administrators clicking at the same moment must not both write.
    with transaction.atomic():
        locked = DefectTriage.objects.select_for_update().get(id=triage_id)
        if locked.state != DefectTriage.State.AWAITING_REVIEW:
            raise DecisionRejected(409, detail="Решение уже принято.")
        locked.decision = serializer.validated_data["action"]
        locked.decision_note = serializer.validated_data.get("note", "")
        locked.final = serializer.validated_data.get("final", {})
        locked.decided_by = user
        locked.decided_at = timezone.now()
        locked.state = DefectTriage.State.DECIDED
        locked.save()
    return locked


def similar_cases(triage: DefectTriage, k: int = 3) -> list[dict]:
    """Closed cases similar to the classified defect; empty rather than broken when embeddings are down."""
    query = (triage.proposal or {}).get("description") or triage.comment
    if not query.strip():
        return []
    try:
        from defects.triage import case_service

        cases = case_service.find_similar(query, k=k)
    except Exception:
        logger.exception("similar case lookup failed for triage %s", triage.id)
        return []
    return [
        {
            "id": str(case.id),
            "defect_type": case.defect_type,
            "severity": case.severity,
            "description": case.description,
            "cause": case.cause,
            "resolution": case.resolution,
            "distance": round(case.distance, 4),
        }
        for case in cases
    ]
