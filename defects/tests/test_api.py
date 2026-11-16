"""
API tests of the defect review endpoints: permissions, the double-decision race, wrong states, payload checks.
"""
import uuid
from unittest.mock import patch

from django.test import override_settings
from django.utils import timezone

from core.tests import BaseTestCase
from defects.models import DefectCase, DefectTriage, DefectType
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


class ReviewApiTestBase(BaseTestCase):
    def setUp(self):
        from defects.triage.case_service import EmbeddingService
        from knowledge.services.retrieval_service import EmbeddingService as RetrievalEmbedding

        self.work = Work.objects.get(id=WORK_ID)
        self.triage = DefectTriage.objects.create(order_id=ORDER_ID, comment="Коронка не садится")
        self.triage.works.add(self.work)
        for target in ("defects.triage.case_service.EmbeddingService.embed",
                       "knowledge.services.retrieval_service.EmbeddingService.embed"):
            p = patch(target, return_value=[[1.0] * 1024])
            p.start()
            self.addCleanup(p.stop)

    def pause_at_review(self):
        """Simulate the worker having run the graph: the row is paused at review with a proposal."""
        self.triage.proposal = dict(PROPOSAL)
        self.triage.state = DefectTriage.State.AWAITING_REVIEW
        self.triage.save()


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class TriageListTest(ReviewApiTestBase):
    url = "/api/defects/triage/"

    def test_admin_sees_only_pending_triages(self):
        self.triage.state = DefectTriage.State.APPLIED
        self.triage.save()
        decided = DefectTriage.objects.create(order_id=ORDER_ID, comment="Вторая", state=DefectTriage.State.DECIDED)

        self.set_up_for_admin()
        response = self.client.get(self.url, format="json")

        self.assertEqual(response.status_code, 200)
        states = {item["state"] for item in response.data}
        self.assertNotIn("applied", states)
        self.assertIn("decided", states)

    def test_non_admins_are_rejected(self):
        for set_up in (self.set_up_for_physician, self.set_up_for_tech):
            set_up()
            with self.subTest(role=set_up.__name__):
                self.assertEqual(self.client.get(self.url, format="json").status_code, 403)
        from rest_framework.test import APIClient
        self.assertEqual(APIClient().get(self.url, format="json").status_code, 401)  # anonymous


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class TriageDetailTest(ReviewApiTestBase):
    def url(self, triage_id=None):
        return f"/api/defects/triage/{triage_id or self.triage.id}/"

    def test_admin_sees_proposal_and_similar_cases(self):
        self.pause_at_review()
        case = DefectCase.objects.create(
            defect_type=DefectType.FIT, severity="medium", description="Коронка не садится.",
            cause="Малый зазор.", resolution="Увеличить зазор.", search_text="Коронка не садится.",
            embedding=[1.0] * 1024,
        )

        self.set_up_for_admin()
        response = self.client.get(self.url(), format="json")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["proposal"]["operationId"], FIRST_OPERATION_ID)
        self.assertEqual(data["state"], "awaiting_review")
        self.assertEqual([w["id"] for w in data["works"]], [WORK_ID])
        self.assertEqual(data["similarCases"][0]["id"], str(case.id))

    def test_similar_case_lookup_failure_returns_empty_list(self):
        self.pause_at_review()
        with patch("defects.views.case_service.find_similar", side_effect=RuntimeError("embeddings down")):
            self.set_up_for_admin()
            response = self.client.get(self.url(), format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["similarCases"], [])

    def test_non_admins_are_rejected(self):
        self.set_up_for_physician()
        self.assertEqual(self.client.get(self.url(), format="json").status_code, 403)


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class TriageDecisionTest(ReviewApiTestBase):
    def url(self, triage_id=None):
        return f"/api/defects/triage/{triage_id or self.triage.id}/decision"

    def setUp(self):
        super().setUp()
        from accounts.models import User
        self.admin = User.objects.get(email=self.admin_email)
        self.set_up_for_admin()

    def approve_payload(self, **final):
        return {"action": "approve", "note": "", "final": final} if final else {"action": "approve"}

    def test_approve_stores_the_decision_and_the_worker_resumes(self):
        from defects.worker import DefectWorker
        from defects.graph import build_graph
        from langgraph.checkpoint.memory import InMemorySaver
        from defects.tests.test_graph import completion, classification_obj, proposal_obj
        from operations.models import Operation

        # the real path: the worker runs the graph until the review interrupt...
        with patch("llm.service.get_client") as get_client:
            get_client.return_value.chat.completions.parse.side_effect = [
                completion(classification_obj()), completion(proposal_obj(number=1)),
            ]
            worker = DefectWorker(graph=build_graph(InMemorySaver()), poll_interval_s=0)
            self.assertTrue(worker.tick())
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.AWAITING_REVIEW)

        response = self.client.post(self.url(), self.approve_payload(), format="json")

        self.assertEqual(response.status_code, 202)
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.DECIDED)
        self.assertEqual(self.triage.decision, DefectTriage.Decision.APPROVE)
        self.assertEqual(self.triage.decided_by, self.admin)
        self.assertIsNotNone(self.triage.decided_at)
        self.assertEqual(self.triage.final["operation_id"], FIRST_OPERATION_ID)  # taken from the proposal

        # ...and a second worker pass resumes the graph with the stored decision
        with patch("llm.service.get_client"):  # no LLM calls on the resume path
            self.assertTrue(worker.tick())
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(Operation.objects.get(id=FIRST_OPERATION_ID).operation_status.number, 1)

    def test_edit_requires_final_and_uses_the_admin_values(self):
        self.pause_at_review()
        response = self.client.post(self.url(), {"action": "edit"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("final", response.data)

        response = self.client.post(self.url(), {
            "action": "edit",
            "final": {"operationId": FIRST_OPERATION_ID, "likelyCause": "Другая причина.", "recommendation": "Другое."},
        }, format="json")
        self.assertEqual(response.status_code, 202)
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.final["operation_id"], FIRST_OPERATION_ID)
        self.assertEqual(self.triage.final["likely_cause"], "Другая причина.")

    def test_reject_requires_a_note(self):
        self.pause_at_review()
        response = self.client.post(self.url(), {"action": "reject", "note": "   "}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("note", response.data)

        response = self.client.post(self.url(), {"action": "reject", "note": "причина в фрезеровке"}, format="json")
        self.assertEqual(response.status_code, 202)
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.decision_note, "причина в фрезеровке")
        self.assertEqual(self.triage.final, {})

    def test_operation_must_belong_to_the_triage_works(self):
        self.pause_at_review()
        foreign = "00000000-0000-0000-0000-0000000000ff"
        response = self.client.post(self.url(), {
            "action": "edit", "final": {"operationId": foreign},
        }, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("final", response.data)

    def test_double_decision_returns_409(self):
        self.pause_at_review()
        self.assertEqual(self.client.post(self.url(), self.approve_payload(), format="json").status_code, 202)
        response = self.client.post(self.url(), self.approve_payload(), format="json")

        self.assertEqual(response.status_code, 409)
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.DECIDED)  # the first decision stands

    def test_decision_in_the_wrong_state_returns_409(self):
        for state in (DefectTriage.State.SUBMITTED, DefectTriage.State.PROCESSING,
                      DefectTriage.State.APPLIED, DefectTriage.State.FAILED):
            with self.subTest(state=state):
                self.triage.state = state
                self.triage.save()
                response = self.client.post(self.url(), self.approve_payload(), format="json")
                self.assertEqual(response.status_code, 409)

    def test_unknown_action_is_a_payload_error(self):
        self.pause_at_review()
        response = self.client.post(self.url(), {"action": "maybe"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("action", response.data)

    def test_anonymous_is_rejected(self):
        from rest_framework.test import APIClient
        self.pause_at_review()
        self.assertEqual(APIClient().post(self.url(), self.approve_payload(), format="json").status_code, 401)
