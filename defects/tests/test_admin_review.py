"""
Tests of the Django admin review page: it drives the same decision service as the admin API.
"""
from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse

from core.tests import BaseTestCase
from defects.models import DefectTriage
from works.models import Work

WORK_ID = "60b5e09a-9d70-486e-a010-64f3504ce0a9"
ORDER_ID = "c5f7d483-347b-4cbb-93b2-f9de7cd03cc9"
FIRST_OPERATION_ID = "cd14866d-6436-4e0c-b362-d8dcbcdcd1f1"

PROPOSAL = {
    "description": "Коронка не садится.",
    "defect_type": "fit",
    "severity": "medium",
    "operation_id": FIRST_OPERATION_ID,
    "operation_name": "Операция 1",
    "likely_cause": "Малый зазор.",
    "recommendation": "Увеличить зазор.",
}


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class AdminReviewPageTest(BaseTestCase):
    def setUp(self):
        from accounts.models import User
        from defects.triage.case_service import EmbeddingService
        from knowledge.services.retrieval_service import EmbeddingService as RetrievalEmbedding

        self.work = Work.objects.get(id=WORK_ID)
        self.triage = DefectTriage.objects.create(order_id=ORDER_ID, comment="Коронка не садится")
        self.triage.works.add(self.work)
        self.url = reverse("admin:defecttriage-review", args=[self.triage.id])
        # Django admin pages authenticate with a session, not with the JWT the API tests use.
        self.admin_client = self.client_class()
        self.admin_client.force_login(User.objects.get(email=self.admin_email))
        for target in ("defects.triage.case_service.EmbeddingService.embed",
                       "knowledge.services.retrieval_service.EmbeddingService.embed"):
            p = patch(target, return_value=[[1.0] * 1024])
            p.start()
            self.addCleanup(p.stop)

    def worker_pause(self):
        """The real path: the worker runs the graph until the review interrupt."""
        from defects.graph import build_graph
        from defects.worker import DefectWorker
        from defects.tests.test_graph import completion, classification_obj, proposal_obj
        from langgraph.checkpoint.memory import InMemorySaver

        with patch("llm.service.get_client") as get_client:
            get_client.return_value.chat.completions.parse.side_effect = [
                completion(classification_obj()), completion(proposal_obj(number=1)),
            ]
            worker = DefectWorker(graph=build_graph(InMemorySaver()), poll_interval_s=0)
            self.assertTrue(worker.tick())

    def test_page_shows_comment_classification_proposal_and_similar_cases(self):
        self.triage.proposal = dict(PROPOSAL)
        self.triage.state = DefectTriage.State.AWAITING_REVIEW
        self.triage.save()

        response = self.admin_client.get(self.url)

        self.assertEqual(response.status_code, 200)
        content = response.rendered_content
        self.assertIn("Коронка не садится", content)  # comment and classification description
        self.assertIn("Увеличить зазор", content)  # proposal recommendation
        self.assertIn("Утвердить как есть", content)  # the action buttons
        self.assertIn(FIRST_OPERATION_ID, content)  # operation select prefilled with the proposal

    def test_list_has_a_review_link_per_row(self):
        response = self.admin_client.get("/admin/defects/defecttriage/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Открыть разбор")

    def test_approve_stores_the_decision_for_the_worker(self):
        self.worker_pause()

        response = self.admin_client.post(self.url, {"action": "approve"})

        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.DECIDED)
        self.assertEqual(self.triage.decision, DefectTriage.Decision.APPROVE)
        self.assertEqual(self.triage.final["operation_id"], FIRST_OPERATION_ID)  # from the proposal
        self.assertEqual(self.triage.decided_by.email, self.admin_email)

    def test_edit_uses_the_admin_values(self):
        self.worker_pause()

        response = self.admin_client.post(self.url, {
            "action": "edit",
            "operation_id": FIRST_OPERATION_ID,
            "description": "Коронка не садится на 24.",
            "defect_type": "fit",
            "severity": "high",
            "likely_cause": "Другая причина.",
            "recommendation": "Другое решение.",
        })

        self.assertRedirects(response, self.url, fetch_redirect_response=False)
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.final["likely_cause"], "Другая причина.")
        self.assertEqual(self.triage.final["severity"], "high")

    def test_reject_without_note_is_rejected_with_a_message(self):
        self.worker_pause()

        response = self.admin_client.post(self.url, {"action": "reject", "note": "   "})

        self.assertEqual(response.status_code, 200)  # the page re-renders with the error
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.AWAITING_REVIEW)  # nothing stored
        self.assertIn("note", response.rendered_content)

    def test_double_decision_shows_an_error_and_keeps_the_first(self):
        self.worker_pause()
        self.admin_client.post(self.url, {"action": "approve"})

        response = self.admin_client.post(self.url, {"action": "dismiss"})

        self.assertEqual(response.status_code, 200)
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.decision, DefectTriage.Decision.APPROVE)  # the first decision stands
        self.assertIn("не ждёт решения", response.rendered_content)

    def test_non_lab_admin_staff_gets_403(self):
        # a staff user outside the lab-admin group: the admin site lets them in, the review page does not
        from accounts.models import User
        User.objects.create(email="helper@mail.com", first_name="H", last_name="P", is_staff=True)
        self.triage.proposal = dict(PROPOSAL)
        self.triage.state = DefectTriage.State.AWAITING_REVIEW
        self.triage.save()

        helper = self.client_class()
        helper.force_login(User.objects.get(email="helper@mail.com"))
        response = helper.get(self.url)

        self.assertEqual(response.status_code, 403)

