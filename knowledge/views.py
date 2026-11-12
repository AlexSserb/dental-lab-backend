from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import IsLabAdmin, IsTech
from llm.exceptions import LlmError
from knowledge.serializers import KnowledgeAskRequestSerializer, KnowledgeAskResponseSerializer
from knowledge.services.answer_service import AnswerService


class KnowledgeAskThrottle(UserRateThrottle):
    scope = "knowledge_ask"


@extend_schema(
    operation_id="ask_knowledge_base",
    request=KnowledgeAskRequestSerializer,
    responses={200: KnowledgeAskResponseSerializer},
)
@api_view(["POST"])
@permission_classes([IsLabAdmin | IsTech])
@throttle_classes([KnowledgeAskThrottle])
def ask_knowledge_base(request):
    serializer = KnowledgeAskRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        result = AnswerService.ask(
            serializer.validated_data["question"],
            operation_type=serializer.validated_data.get("operation_type"),
            user=request.user,
        )
    except LlmError:  # not configured, timeout, provider down
        return Response({"detail": "База знаний сейчас недоступна. Попробуйте позже."},
                        status=status.HTTP_503_SERVICE_UNAVAILABLE)
    return Response(KnowledgeAskResponseSerializer(result).data)
