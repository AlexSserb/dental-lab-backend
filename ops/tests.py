"""
Tests of the ops endpoints and the monitoring digest: the webhook token check, the email forwarding
and the digest content over known data. No LLM calls happen here.
"""
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core.tests import BaseTestCase
from defects.models import DefectTriage
from llm.models import LlmCallLog
from ops.monitoring import llm_stats, percentile, triage_health

WEBHOOK_URL = "/api/ops/alerts/"
PAYLOAD = {
    "type": "error_rate",
    "message": "Error rate 35% exceeded 10% over the last 30 min",
    "project_name": "dental-lab",
    "run_url": "https://smith.langchain.com/o/x/projects/p?run=a",
}


@override_settings(ALERT_WEBHOOK_TOKEN="secret-token", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@override_settings(EMAIL_ADMIN="ops@example.com")
class AlertWebhookTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unknown_or_missing_token_is_forbidden(self):
        for headers in ({}, {"X-Alert-Token": "wrong"}):
            with self.subTest(headers=headers):
                self.assertEqual(self.client.post(WEBHOOK_URL, PAYLOAD, format="json", headers=headers).status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    def test_empty_token_disables_the_endpoint(self):
        with override_settings(ALERT_WEBHOOK_TOKEN=""):
            self.assertEqual(
                self.client.post(WEBHOOK_URL, PAYLOAD, format="json", headers={"X-Alert-Token": ""}).status_code,
                403,
            )

    def test_valid_token_forwards_the_alert_as_email(self):
        response = self.client.post(WEBHOOK_URL, PAYLOAD, format="json", headers={"X-Alert-Token": "secret-token"})

        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, "LangSmith alert")
        self.assertIn("error_rate", message.body)
        self.assertIn("Error rate 35%", message.body)
        self.assertIn(PAYLOAD["run_url"], message.body)
        self.assertEqual(message.to, ["ops@example.com"])

    def test_mail_failure_is_5xx_so_langsmith_can_retry(self):
        with patch("ops.views.send_mail", side_effect=RuntimeError("smtp down")):
            response = self.client.post(WEBHOOK_URL, PAYLOAD, format="json", headers={"X-Alert-Token": "secret-token"})
        self.assertEqual(response.status_code, 503)

    def test_unknown_payload_shapes_are_tolerated(self):
        for payload in ("plain text", [1, 2, 3], {"alert": {"title": "Latency", "value": 42}}):
            with self.subTest(payload=payload):
                response = self.client.post(WEBHOOK_URL, payload, format="json", headers={"X-Alert-Token": "secret-token"})
                self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 3)


class MonitoringTest(BaseTestCase):
    def setUp(self):
        self.feature = "defect_classify"
        for success, latency in ((True, 1.0), (True, 2.0), (True, 3.0), (False, 9.0)):
            LlmCallLog.objects.create(feature=self.feature, model="m", latency=latency, success=success,
                                      prompt_tokens=10, completion_tokens=5)
        stale = LlmCallLog.objects.create(feature=self.feature, model="m", latency=100.0, success=True)
        LlmCallLog.objects.filter(id=stale.id).update(created_at=timezone.now() - timedelta(days=5))

    def test_llm_stats_aggregates_within_the_window(self):
        stats = llm_stats(hours=24)
        self.assertEqual(len(stats), 1)
        row = stats[0]
        self.assertEqual(row["total"], 4)
        self.assertEqual(row["ok"], 3)
        self.assertAlmostEqual(row["success_rate"], 0.75)
        self.assertAlmostEqual(row["p50"], 2.0)
        self.assertAlmostEqual(row["p95"], 9.0)  # nearest-rank over [1.0, 2.0, 3.0, 9.0]
        self.assertEqual(row["tokens"], 4 * 15)

    def test_percentile_of_empty_list_is_zero(self):
        self.assertEqual(percentile([], 0.95), 0.0)

    def test_triage_health_counts_states_and_failures(self):
        triage = DefectTriage.objects.create(order_id="c5f7d483-347b-4cbb-93b2-f9de7cd03cc9",
                                             comment="Разбирается", state=DefectTriage.State.AWAITING_REVIEW)
        failed = DefectTriage.objects.create(order_id="c5f7d483-347b-4cbb-93b2-f9de7cd03cc9",
                                             comment="Сломался", state=DefectTriage.State.FAILED,
                                             error="boom")
        DefectTriage.objects.filter(id=failed.id).update(created_at=timezone.now() - timedelta(hours=2))

        health = triage_health()
        self.assertEqual(health["counts"].get(DefectTriage.State.FAILED), 1)
        _oldest_created_at, oldest_id = health["oldest_awaiting_review"]
        self.assertEqual(oldest_id, triage.id)
        failed_ids = [row[0] for row in health["failed"]]
        self.assertIn(failed.id, failed_ids)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", EMAIL_ADMIN="ops@example.com")
class DigestCommandTest(BaseTestCase):
    def test_digest_prints_stats_and_triage_health(self):
        import io
        from django.core.management import call_command

        LlmCallLog.objects.create(feature="defect_classify", model="m", latency=2.0, success=True,
                                  prompt_tokens=10, completion_tokens=5)
        DefectTriage.objects.create(order_id="c5f7d483-347b-4cbb-93b2-f9de7cd03cc9",
                                    comment="Сломался", state=DefectTriage.State.FAILED, error="embedding down")

        out_io = io.StringIO()
        call_command("monitoring_digest", stdout=out_io)
        out = out_io.getvalue()

        self.assertIn("defect_classify", out)
        self.assertIn("успех 100%", out)
        self.assertIn("Ошибка обработки", out)
        self.assertIn("embedding down", out)

    def test_digest_email_goes_to_admin(self):
        from django.core.management import call_command

        call_command("monitoring_digest", email=True, stdout=__import__("io").StringIO())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ops@example.com"])
