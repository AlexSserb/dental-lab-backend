"""
Worker tests: the same fake LLM as the graph tests, but the worker - not the test - drives the graph.
"""
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from core.tests import BaseTestCase
from defects.graph import build_graph
from defects.models import DefectTriage
from defects.worker import DefectWorker
from langgraph.checkpoint.memory import InMemorySaver
from llm.exceptions import LlmUnavailable
from operations.models import Operation, OperationStatus
from works.models import Work

WORK_ID = "60b5e09a-9d70-486e-a010-64f3504ce0a9"
ORDER_ID = "c5f7d483-347b-4cbb-93b2-f9de7cd03cc9"
OTHER_ORDER_ID = "68eb5be8-d29f-4a6c-ac64-5be9740fb3f3"
FIRST_OPERATION_ID = "cd14866d-6436-4e0c-b362-d8dcbcdcd1f1"

# imported here so the patch targets resolve after the modules are loaded
from defects.tests.test_graph import FakeLlm, completion, classification_obj, proposal_obj  # noqa: E402


class WorkerTestBase(BaseTestCase):
    def setUp(self):
        from accounts.models import User

        self.work = Work.objects.get(id=WORK_ID)
        self.triage = DefectTriage.objects.create(order_id=ORDER_ID, comment="Коронка не садится")
        self.triage.works.add(self.work)
        self.worker = DefectWorker(graph=build_graph(InMemorySaver()), poll_interval_s=0)
        self.admin_id = str(User.objects.get(email=self.admin_email).id)

        for target in ("defects.triage.case_service.EmbeddingService.embed",
                       "knowledge.services.retrieval_service.EmbeddingService.embed"):
            p = patch(target, return_value=[[1.0] * 1024])
            p.start()
            self.addCleanup(p.stop)

    def fake_llm(self, responses) -> FakeLlm:
        client = FakeLlm(responses)
        p = patch("llm.service.get_client", return_value=client)
        p.start()
        self.addCleanup(p.stop)
        return client

    def decide(self, **decision):
        """The administrator answered through the API: the decision is stored on the row, the state moves on."""
        self.triage.decision = decision.pop("action")
        self.triage.decision_note = decision.pop("note", "")
        self.triage.final = decision.pop("final", {})
        self.triage.decided_by_id = decision.pop("decided_by_id", None) or self.admin_id
        self.triage.decided_at = timezone.now()
        self.triage.state = DefectTriage.State.DECIDED
        self.triage.save()


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class WorkerFlowTest(WorkerTestBase):
    def test_submitted_row_runs_until_the_review_interrupt(self):
        client = self.fake_llm([completion(classification_obj()), completion(proposal_obj(number=1))])

        self.assertTrue(self.worker.tick())

        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.AWAITING_REVIEW)
        self.assertEqual(self.triage.proposal["operation_id"], FIRST_OPERATION_ID)
        self.assertEqual(client.parse.call_count, 2)  # classify + propose, then the graph paused

        # a SUBMITTED row is claimed exactly once: the next pass has nothing to do
        self.assertFalse(self.worker.tick())
        self.assertEqual(client.parse.call_count, 2)

    def test_decided_row_is_resumed_with_the_row_decision(self):
        self.fake_llm([completion(classification_obj()), completion(proposal_obj(number=1))])
        self.worker.tick()  # -> paused at review

        self.decide(
            action=DefectTriage.Decision.APPROVE,
            final={"operation_id": FIRST_OPERATION_ID, "likely_cause": "Малый зазор.", "recommendation": "Увеличить зазор."},
        )
        self.assertTrue(self.worker.tick())  # resumes with Command(resume=...)

        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.APPLIED)
        self.assertIsNotNone(self.triage.applied_at)
        self.assertEqual(str(self.triage.decided_by_id), self.admin_id)
        self.assertEqual(Operation.objects.get(id=FIRST_OPERATION_ID).operation_status.number, 1)

        self.assertFalse(self.worker.tick())  # everything drained

    def test_reject_decision_is_resumed_back_to_propose(self):
        self.fake_llm([
            completion(classification_obj()), completion(proposal_obj(number=1)),
            completion(proposal_obj(number=1)),
        ])
        self.worker.tick()

        self.decide(action=DefectTriage.Decision.REJECT, note="причина в фрезеровке")
        self.assertTrue(self.worker.tick())

        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.AWAITING_REVIEW)  # a new proposal is waiting
        self.assertEqual(self.triage.revisions, 1)

    def test_llm_outage_pauses_at_manual_review(self):
        # The graph handles an LLM outage itself (manual review), so this is NOT a worker failure:
        # the row is parked where the administrator can see it.
        self.fake_llm([LlmUnavailable("simulated outage")])
        self.assertTrue(self.worker.tick())

        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.PROCESSING)  # paused at the review interrupt

    def test_unexpected_failure_marks_failed_and_the_worker_keeps_polling(self):
        # A crash outside the graph's handled errors (DB down, a bug): the row is marked FAILED, the worker lives on.
        graph = MagicMock()
        graph.invoke.side_effect = RuntimeError("boom")
        worker = DefectWorker(graph=graph, poll_interval_s=0)

        self.assertTrue(worker.tick())  # picks the row up and fails

        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.FAILED)
        self.assertIn("RuntimeError: boom", self.triage.error)

        self.assertFalse(worker.tick())  # FAILED rows are not claimed again, the worker just keeps polling


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class ClaimTest(WorkerTestBase):
    def test_submitted_rows_are_claimed_before_decided_ones(self):
        self.fake_llm([
            completion(classification_obj()), completion(proposal_obj(number=1)),
            completion(classification_obj(confidence="low")),  # the second row: vague report -> manual review
        ])
        self.worker.tick()  # the first row pauses at review
        self.decide(action=DefectTriage.Decision.DISMISS)  # the administrator answered: first row is DECIDED now
        second = DefectTriage.objects.create(order_id=OTHER_ORDER_ID, comment="Вторая проблема")  # SUBMITTED

        self.assertTrue(self.worker.tick())  # submitted has priority
        second.refresh_from_db()
        self.triage.refresh_from_db()
        self.assertEqual(second.state, DefectTriage.State.PROCESSING)  # claimed and driven
        self.assertEqual(self.triage.state, DefectTriage.State.DECIDED)  # still waiting for its turn

        self.assertTrue(self.worker.tick())  # now the decided row is resumed
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.REJECTED)  # dismissed


class LockedRowTest(TransactionTestCase):
    """
    SKIP LOCKED can only be proven from a second connection, which must also see a committed row -
    so this test runs outside the wrapping transaction and loads its own fixtures.
    """

    fixtures = [
        "./accounts/fixtures/test_data/groups.json",
        "./accounts/fixtures/test_data/customers.json",
        "./accounts/fixtures/test_data/users.json",
        "./core/fixtures/test_data/statuses.json",
        "./core/fixtures/test_data/object_types.json",
        "./core/fixtures/test_data/orders.json",
        "./core/fixtures/test_data/works.json",
        "./core/fixtures/test_data/operations.json",
    ]

    def setUp(self):
        self.triage = DefectTriage.objects.create(order_id=ORDER_ID, comment="Коронка не садится")
        self.worker = DefectWorker(graph=build_graph(InMemorySaver()), poll_interval_s=0)

    def test_locked_row_is_skipped_and_taken_later(self):
        import psycopg

        # the graph run after the release ends in manual review: an outage makes no further LLM calls
        with patch("llm.service.get_client") as get_client:
            get_client.return_value.chat.completions.parse.side_effect = LlmUnavailable("simulated outage")

            db = settings.DATABASES["default"]
            other_worker = psycopg.connect(
                host=db["HOST"] or "localhost", port=int(db.get("PORT") or 5432), dbname=db["NAME"],
                user=db["USER"], password=db["PASSWORD"],
            )
            try:
                with other_worker.transaction():
                    # worker #1 claims the row and holds its lock while "processing"
                    other_worker.execute("SELECT id FROM defects_defecttriage WHERE id = %s FOR UPDATE",
                                         (str(self.triage.id),))
                    # worker #2 polls: the locked row is skipped, nothing else to do
                    self.assertFalse(self.worker.tick())
                    self.triage.refresh_from_db()
                    self.assertEqual(self.triage.state, DefectTriage.State.SUBMITTED)  # untouched by worker #2
            finally:
                other_worker.close()

            # worker #1 released the row without finishing: worker #2 (or the next poll) takes it now
            self.assertTrue(self.worker.tick())
        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.PROCESSING)  # claimed, paused at review


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class RunDefectWorkerCommandTest(WorkerTestBase):
    """The management command wires the real PostgresSaver with an idempotent setup()."""

    def test_once_pass_processes_a_submitted_row(self):
        self.fake_llm([completion(classification_obj()), completion(proposal_obj(number=1))])
        from django.core.management import call_command

        call_command("run_defect_worker", "--once", verbosity=0)

        self.triage.refresh_from_db()
        self.assertEqual(self.triage.state, DefectTriage.State.AWAITING_REVIEW)
