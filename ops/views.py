"""
The ops API: infrastructure-facing endpoints (no JWT).

The LangSmith alert webhook: alert rules configured in the LangSmith UI (error rate, latency, cost)
POST here, and the alert becomes an email to EMAIL_ADMIN. Authenticated with a shared token instead of
JWT, because LangSmith cannot present our user tokens; the token must be set (empty = endpoint disabled).
"""
import logging
import secrets

from django.conf import settings
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

TOKEN_HEADER = "X-Alert-Token"
MAX_MESSAGE_LENGTH = 4000


class LangSmithAlertWebhookView(APIView):
    """Receive LangSmith alert-rule callbacks and forward them to EMAIL_ADMIN."""

    authentication_classes: list = []
    permission_classes: list = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "alert_webhook"

    @extend_schema(exclude=True)
    def post(self, request: Request) -> Response:
        supplied = request.headers.get(TOKEN_HEADER, "")
        if not settings.ALERT_WEBHOOK_TOKEN or not secrets.compare_digest(supplied, settings.ALERT_WEBHOOK_TOKEN):
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        message = _format_alert(request.data)
        try:
            send_mail(
                subject="LangSmith alert",
                message=message[:MAX_MESSAGE_LENGTH],
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.EMAIL_ADMIN],
                fail_silently=False,
            )
        except Exception as exc:
            # A 5xx lets LangSmith retry the webhook instead of silently dropping the alert.
            logger.exception("failed to forward a LangSmith alert")
            return Response({"detail": f"failed to forward the alert: {exc}"}, status=503)
        return Response({"detail": "alert forwarded"}, status=status.HTTP_202_ACCEPTED)


def _format_alert(payload) -> str:
    """LangSmith alert payloads vary by rule type; keep it tolerant — every field we know goes into the mail."""
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return repr(payload)

    alert = payload.get("alert") if isinstance(payload.get("alert"), dict) else payload
    lines = []
    for label, key in (("Тип", ("type", "name", "title")),
                       ("Сообщение", ("message", "text", "description")),
                       ("Проект", ("project", "project_name")),
                       ("Метрика", ("metric", "metric_name")),
                       ("Значение", ("value", "current_value")),
                       ("Порог", ("threshold", "threshold_value")),
                       ("Run", ("run_url", "url"))):
        for key_variant in key:
            value = alert.get(key_variant) if alert.get(key_variant) is not None else payload.get(key_variant)
            if value:
                lines.append(f"{label}: {value}")
                break
    return "\n".join(lines) or repr(payload)
