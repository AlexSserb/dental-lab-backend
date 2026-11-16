"""The admin-only review API of the defect triage workflow."""
import logging

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle

from accounts.permissions import IsLabAdmin
from defects.models import DefectTriage
from defects.serializers import TriageDecisionSerializer, TriageDetailSerializer, TriageListItemSerializer
from defects.triage import case_service

logger = logging.getLogger(__name__)

PENDING_LIST_LIMIT = 100


class DefectDecisionThrottle(ScopedRateThrottle):
    """Guards the decision endpoint: one administrator click must not flood the worker with resumes."""

    scope = "defect_decision"


@extend_schema(
    operation_id="list_defect_triages",
    responses={200: TriageListItemSerializer(many=True)},
    summary="Pending defect triages (submitted, processing, awaiting review, decided)",
)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def triage_list(request):
    triages = DefectTriage.objects.filter(state__in=DefectTriage.OPEN_STATES).order_by("-created_at")
    serializer = TriageListItemSerializer(triages[:PENDING_LIST_LIMIT], many=True)
    return Response(serializer.data)


@extend_schema(
    operation_id="get_defect_triage",
    responses={200: TriageDetailSerializer, 404: OpenApiResponse(description="Unknown triage")},
    summary="One triage: the proposal, the works and similar closed cases",
)
@api_view(["GET"])
@permission_classes([IsLabAdmin])
def triage_detail(request, triage_id: str):
    triage = get_object_or_404(DefectTriage, id=triage_id)
    data = TriageDetailSerializer(triage).data
    data["works"] = [{"id": str(work.id), "name": work.work_type.name} for work in
                     triage.works.select_related("work_type")]
    data["similar_cases"] = _similar_cases(triage)
    return Response(data)


@extend_schema(
    operation_id="decide_defect_triage",
    request=TriageDecisionSerializer,
    responses={
        202: OpenApiResponse(description="Decision stored; the worker resumes the graph"),
        400: OpenApiResponse(description="Invalid decision payload"),
        404: OpenApiResponse(description="Unknown triage"),
        409: OpenApiResponse(description="The triage is not awaiting a review (already decided, closed, failed)"),
    },
    summary="Approve, edit, reject or dismiss a triage (the worker picks it up)",
)
@api_view(["POST"])
@permission_classes([IsLabAdmin])
@throttle_classes([DefectDecisionThrottle])
def triage_decision(request, triage_id: str):
    triage = get_object_or_404(DefectTriage, id=triage_id)
    # Double decision and wrong state are rejected before validation: 409, not a payload error.
    if triage.state != DefectTriage.State.AWAITING_REVIEW:
        return Response(
            {"detail": f"Разбор не ждёт решения (состояние: {triage.get_state_display()})."},
            status=status.HTTP_409_CONFLICT,
        )

    serializer = TriageDecisionSerializer(data=request.data, context={"triage": triage})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Re-checked under a lock: two administrators clicking at the same moment must not both write.
    with transaction.atomic():
        locked = DefectTriage.objects.select_for_update().get(id=triage.id)
        if locked.state != DefectTriage.State.AWAITING_REVIEW:
            return Response({"detail": "Решение уже принято."}, status=status.HTTP_409_CONFLICT)
        locked.decision = serializer.validated_data["action"]
        locked.decision_note = serializer.validated_data.get("note", "")
        locked.final = serializer.validated_data.get("final", {})
        locked.decided_by = request.user
        locked.decided_at = timezone.now()
        locked.state = DefectTriage.State.DECIDED
        locked.save()
    return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)


def _similar_cases(triage: DefectTriage) -> list[dict]:
    """Closed cases similar to the classified defect; empty rather than broken when embeddings are down."""
    query = (triage.proposal or {}).get("description") or triage.comment
    if not query.strip():
        return []
    try:
        cases = case_service.find_similar(query, k=3)
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
