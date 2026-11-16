"""
Graph tests with a fake LLM: the fake OpenAI client stands in at llm.service.get_client, so the real
classify_defect, propose_redo, validators and prompts run - only the HTTP call is replaced.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import override_settings

from core.tests import BaseTestCase
from defects.graph import MAX_REVISIONS, apply_node, build_graph
from defects.models import DefectCase, DefectTriage
from defects.triage.schemas import DefectClassification, RedoProposal
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from llm.exceptions import LlmUnavailable
from llm.models import LlmCallLog
from operations.models import Operation, OperationStatus
from works.models import Work

WORK_ID = "60b5e09a-9d70-486e-a010-64f3504ce0a9"
ORDER_ID = "c5f7d483-347b-4cbb-93b2-f9de7cd03cc9"
# Fixture operations of WORK_ID; the first candidate of propose_redo is the one with the lowest ordinal.
FIRST_OPERATION_ID = "cd14866d-6436-4e0c-b362-d8dcbcdcd1f1"
SECOND_OPERATION_ID = "519beb85-e9a9-43a3-a753-16ed36d4de48"


def unit_vector(index: int) -> list[float]:
    vector = [0.0] * 1024
    vector[index] = 1.0
    return vector


def classification_obj(**overrides) -> DefectClassification:
    data = {"description": "Коронка не садится.", "defect_type": "fit", "severity": "medium", "confidence": "high"}
    return DefectClassification(**{**data, **overrides})


def proposal_obj(number=1) -> RedoProposal:
    return RedoProposal(operation_number=number, likely_cause="Малый зазор.", recommendation="Увеличить зазор.")


def completion(parsed) -> SimpleNamespace:
    """The slice of an OpenAI completion that call_structured reads."""
    msg = SimpleNamespace(parsed=parsed, refusal=None, content=parsed.model_dump_json())
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=SimpleNamespace(prompt_tokens=100, completion_tokens=20))


class FakeLlm:
    """Stands in for the OpenAI client: chat.completions.parse returns the prepared objects in order."""

    def __init__(self, responses):
        self.parse = MagicMock(side_effect=list(responses))
        self.chat = SimpleNamespace(completions=SimpleNamespace(parse=self.parse))


class GraphTestBase(BaseTestCase):
    def setUp(self):
        self.work = Work.objects.get(id=WORK_ID)
        self.triage = DefectTriage.objects.create(order_id=ORDER_ID, comment="Коронка не садится")
        self.triage.works.add(self.work)
        self.config = {"configurable": {"thread_id": self.triage.thread_id}}
        from accounts.models import User
        self.admin_id = str(User.objects.get(email=self.admin_email).id)
        self.other_op = Operation.objects.create(  # a second candidate the admin may pick in the edit flow
            work=self.work, operation_type=Operation.objects.first().operation_type,
            ordinal_number=99, operation_status=OperationStatus.get_default_status(),
        )
        self._offline_embeddings()

    def _offline_embeddings(self):
        """Case store and KB retrieval embed nothing over the network."""
        for target in ("defects.triage.case_service.EmbeddingService.embed",
                       "knowledge.services.retrieval_service.EmbeddingService.embed"):
            p = patch(target, return_value=[unit_vector(0)])
            p.start()
            self.addCleanup(p.stop)

    def fake_llm(self, responses) -> FakeLlm:
        client = FakeLlm(responses)
        p = patch("llm.service.get_client", return_value=client)
        p.start()
        self.addCleanup(p.stop)
        return client

    def graph_with(self, checkpointer=None):
        self.saver = checkpointer or InMemorySaver()
        self.graph = build_graph(self.saver)
        return self.graph

    def run_to_review(self, responses) -> FakeLlm:
        """First 'process': run the graph with the fake LLM until the review interrupt."""
        client = self.fake_llm(responses)
        self.graph_with().invoke({"triage_id": str(self.triage.id)}, config=self.config)
        return client

    def snapshot(self):
        state = self.graph.get_state(self.config)
        return state.values, state.next

    def approve(self, **final) -> dict:
        decision = {"action": "approve", "note": "", "decided_by_id": self.admin_id}
        if final:
            decision["final"] = final
        return decision

    def assert_paused_at_review(self, manual=False):
        values, next_nodes = self.snapshot()
        self.assertEqual(next_nodes, ("review",))
        self.assertEqual(values.get("manual"), manual)
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.AWAITING_REVIEW if not manual else DefectTriage.State.PROCESSING)
        return values


@override_settings(PROMPT_SOURCE="local", AI_MODEL="fake", AI_API_KEY="k", AI_MAX_RETRIES=1)
class FakeLlmFlowTest(GraphTestBase):
    """The seven flows of step 8: the whole graph runs, only the LLM transport is fake."""

    def test_approve_flow(self):
        client = self.run_to_review([completion(classification_obj()), completion(proposal_obj(number=1))])

        # paused with a proposal; the real pipeline produced it from the local prompt and the real candidates
        values = self.assert_paused_at_review()
        self.assertEqual(values["proposal"]["operation_id"], FIRST_OPERATION_ID)
        self.assertEqual(client.parse.call_count, 2)
        self.assertIn("classify a reported defect", client.parse.call_args_list[0].kwargs["messages"][0]["content"])
        self.assertIn("must be redone", client.parse.call_args_list[1].kwargs["messages"][0]["content"])
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.decision, "")  # review wrote nothing while paused

        result = self.graph.invoke(Command(resume=self.approve(
            operation_id=FIRST_OPERATION_ID, likely_cause="Малый зазор.", recommendation="Увеличить зазор.",
        )), config=self.config)

        self.assertTrue(result["notified"])
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(triage.decision, DefectTriage.Decision.APPROVE)
        self.assertEqual(triage.final["operation_id"], FIRST_OPERATION_ID)
        self.assertIsNotNone(triage.applied_at)
        self.assertIsNotNone(triage.notified_at)
        operation = Operation.objects.get(id=FIRST_OPERATION_ID)
        self.assertEqual(operation.operation_status.number, 1)  # sent back to the queue
        self.assertIsNone(operation.exec_start)
        self.assertTrue(operation.is_exec_start_editable)
        self.assertEqual(DefectCase.objects.filter(triage=triage).count(), 1)  # closed case stored as precedent

    def test_edit_flow_applies_the_admin_values(self):
        self.run_to_review([completion(classification_obj()), completion(proposal_obj(number=1))])
        admin_values = {"operation_id": str(self.other_op.id), "likely_cause": "Другая причина.",
                        "recommendation": "Другое решение."}

        self.graph.invoke(Command(resume={
            "action": "edit", "note": "фрезеровка, а не подготовка", "final": admin_values,
            "decided_by_id": self.admin_id,
        }), config=self.config)

        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(triage.decision, DefectTriage.Decision.EDIT)
        self.assertEqual(triage.final, admin_values)
        self.assertEqual(triage.decision_note, "фрезеровка, а не подготовка")
        self.assertEqual(Operation.objects.get(id=self.other_op.id).operation_status.number, 1)
        # the operation the model proposed is untouched
        self.assertNotEqual(Operation.objects.get(id=FIRST_OPERATION_ID).operation_status.number, 1)

    def test_reject_then_repropose_then_approve(self):
        client = self.run_to_review([
            completion(classification_obj()), completion(proposal_obj(number=1)), completion(proposal_obj(number=2)),
        ])

        self.graph.invoke(Command(resume={
            "action": "reject", "note": "причина в фрезеровке", "decided_by_id": self.admin_id,
        }), config=self.config)
        values = self.assert_paused_at_review()  # back at the gate with a new proposal
        self.assertEqual(values["proposal"]["operation_id"], SECOND_OPERATION_ID)
        self.assertEqual(client.parse.call_count, 3)

        # the administrator's note reached the second proposal attempt as feedback
        user_text = client.parse.call_args_list[2].kwargs["messages"][1]["content"]
        self.assertIn("<feedback>причина в фрезеровке</feedback>", user_text)
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.revisions, 1)

        self.graph.invoke(Command(resume=self.approve(
            operation_id=SECOND_OPERATION_ID, likely_cause="Малый зазор.",
            recommendation="Увеличить зазор.",
        )), config=self.config)
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(triage.revisions, 1)

    def test_max_revision_cutoff(self):
        self.triage.revisions = MAX_REVISIONS  # the budget is spent
        self.triage.save(update_fields=["revisions"])
        client = self.run_to_review([completion(classification_obj())])

        values = self.assert_paused_at_review(manual=True)  # review with no proposal
        self.assertIsNone(values.get("proposal"))
        self.assertIn("revision limit", values["error"])
        self.assertEqual(client.parse.call_count, 1)  # classify ran, propose never did

        # manual review: the administrator supplies the values themselves
        self.graph.invoke(Command(resume={
            "action": "edit", "note": "", "final": {"operation_id": str(self.other_op.id)},
            "decided_by_id": self.admin_id,
        }), config=self.config)
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(triage.final["operation_id"], str(self.other_op.id))

    def test_llm_down_goes_to_manual_review(self):
        client = self.run_to_review([LlmUnavailable("simulated outage")])

        values = self.assert_paused_at_review(manual=True)
        self.assertIn("classification failed", values["error"])
        self.assertIsNone(values.get("proposal"))
        self.assertEqual(client.parse.call_count, 1)
        self.assertFalse(LlmCallLog.objects.get().success)  # the failure was logged

        self.graph.invoke(Command(resume={
            "action": "edit", "note": "ручной разбор", "final": {"operation_id": str(self.other_op.id)},
            "decided_by_id": self.admin_id,
        }), config=self.config)
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.APPLIED)

    def test_resume_after_simulated_restart(self):
        # "process 1" runs until the interrupt; then the process dies. "process 2" rebuilds everything and
        # resumes from the same checkpointer - the paused state must not live in any process memory.
        saver = InMemorySaver()
        client = self.fake_llm([completion(classification_obj()), completion(proposal_obj(number=1))])
        self.graph = build_graph(saver)
        self.graph.invoke({"triage_id": str(self.triage.id)}, config=self.config)

        fresh_client = self.fake_llm([])  # a new process would have no LLM state either
        self.graph = build_graph(saver)

        values, next_nodes = self.snapshot()
        self.assertEqual(next_nodes, ("review",))
        self.assertEqual(values["proposal"]["operation_id"], FIRST_OPERATION_ID)

        result = self.graph.invoke(Command(resume=self.approve(operation_id=FIRST_OPERATION_ID)), config=self.config)

        self.assertTrue(result["notified"])
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.APPLIED)
        fresh_client.parse.assert_not_called()  # the resumed process did not re-run any LLM node

    def test_apply_called_twice_is_idempotent(self):
        self.run_to_review([completion(classification_obj()), completion(proposal_obj(number=1))])
        self.graph.invoke(Command(resume=self.approve(
            operation_id=FIRST_OPERATION_ID, likely_cause="Малый зазор.", recommendation="Увеличить зазор.",
        )), config=self.config)
        triage = DefectTriage.objects.get(id=self.triage.id)
        applied_at = triage.applied_at

        # a duplicated decision (replay, double click, restarted worker) must not reset the operation again
        apply_node({"triage_id": str(self.triage.id), "decision": self.approve(
            operation_id=FIRST_OPERATION_ID, likely_cause="Малый зазор.", recommendation="Увеличить зазор.",
        )})

        triage.refresh_from_db()
        self.assertEqual(triage.applied_at, applied_at)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(DefectCase.objects.filter(triage=triage).count(), 1)  # the case was not duplicated


class DismissFlowTest(GraphTestBase):
    def test_dismiss_closes_without_changes(self):
        self.run_to_review([completion(classification_obj()), completion(proposal_obj(number=1))])
        self.graph.invoke(Command(resume={
            "action": "dismiss", "note": "не дефект", "decided_by_id": self.admin_id,
        }), config=self.config)
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.REJECTED)
        self.assertEqual(triage.final, {})
        self.assertIsNone(triage.applied_at)
        self.assertNotEqual(Operation.objects.get(id=FIRST_OPERATION_ID).operation_status.number, 1)


class ManualApproveWithoutOperationTest(GraphTestBase):
    def test_manual_approve_without_operation_closes_as_rejected(self):
        self.run_to_review([LlmUnavailable("simulated outage")])
        self.graph.invoke(Command(resume=self.approve()), config=self.config)  # nothing to apply
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.REJECTED)
        self.assertIsNone(triage.applied_at)


class NotifyNodeTest(GraphTestBase):
    def test_notify_survives_embedding_failure(self):
        self.run_to_review([completion(classification_obj()), completion(proposal_obj(number=1))])
        with patch("defects.graph.add_case", side_effect=RuntimeError("embedding endpoint down")):
            result = self.graph.invoke(Command(resume=self.approve(operation_id=FIRST_OPERATION_ID)), config=self.config)
        self.assertTrue(result["notified"])  # the workflow still finishes
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.APPLIED)
        self.assertIsNotNone(DefectTriage.objects.get(id=self.triage.id).notified_at)


class RetrievalFailureTest(GraphTestBase):
    def test_retrieval_failure_goes_manual(self):
        client = self.fake_llm([completion(classification_obj())])
        with patch("defects.graph.get_precedents", side_effect=RuntimeError("embeddings down")):
            self.graph_with().invoke({"triage_id": str(self.triage.id)}, config=self.config)
        values, next_nodes = self.snapshot()
        self.assertEqual(next_nodes, ("review",))
        self.assertTrue(values["manual"])
        self.assertIn("precedent retrieval failed", values["error"])
        self.assertEqual(client.parse.call_count, 1)  # propose never ran


class LowConfidenceTest(GraphTestBase):
    def test_low_confidence_goes_manual(self):
        self.run_to_review([completion(classification_obj(confidence="low"))])
        values = self.assert_paused_at_review(manual=True)
        self.assertEqual(values["classification"]["confidence"], "low")


class PostgresCheckpointerTest(GraphTestBase):
    """Integration: pause and resume through the Postgres checkpointer used in production."""

    def test_graph_pauses_and_resumes_across_postgres_checkpoints(self):
        from langgraph.checkpoint.postgres import PostgresSaver

        db = settings.DATABASES["default"]
        dsn = (
            f"host={db['HOST'] or 'localhost'} port={db.get('PORT', 5432)} dbname={db['NAME']} "
            f"user={db['USER']} password={db['PASSWORD']}"
        )
        with PostgresSaver.from_conn_string(dsn) as checkpointer:
            checkpointer.setup()
            client = self.fake_llm([completion(classification_obj()), completion(proposal_obj(number=1))])
            self.graph = build_graph(checkpointer)  # the whole flow, pause included, lives in Postgres
            self.graph.invoke({"triage_id": str(self.triage.id)}, config=self.config)

            # a brand-new graph over the same Postgres checkpointer sees the pause and resumes it
            self.graph = build_graph(checkpointer)
            values, next_nodes = self.snapshot()
            self.assertEqual(next_nodes, ("review",))
            self.assertEqual(values["proposal"]["operation_id"], FIRST_OPERATION_ID)
            self.assertEqual(client.parse.call_count, 2)

            result = self.graph.invoke(Command(resume=self.approve(operation_id=FIRST_OPERATION_ID)), config=self.config)
        self.assertTrue(result["notified"])
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.APPLIED)
