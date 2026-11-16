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
from defects.review import similar_cases
from defects.serializers import TriageDecisionSerializer, TriageDetailSerializer, TriageListItemSerializer

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
    data["similar_cases"] = similar_cases(triage)
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
    from defects.review import DecisionRejected, decide

    try:
        decide(triage_id, request.user, request.data)
    except DecisionRejected as rejected:
        body = rejected.errors or {"detail": rejected.detail}
        return Response(body, status=rejected.status)
    return Response({"status": "accepted"}, status=status.HTTP_202_ACCEPTED)

