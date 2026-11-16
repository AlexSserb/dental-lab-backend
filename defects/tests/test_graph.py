from types import SimpleNamespace
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase

from core.tests import BaseTestCase
from defects.graph import MAX_REVISIONS, apply_node, build_graph
from defects.models import DefectCase, DefectTriage
from defects.triage.propose import RedoDecision
from defects.triage.schemas import DefectClassification, RedoProposal
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from operations.models import Operation, OperationStatus
from works.models import Work

WORK_ID = "60b5e09a-9d70-486e-a010-64f3504ce0a9"
ORDER_ID = "c5f7d483-347b-4cbb-93b2-f9de7cd03cc9"
RESET_OPERATION_ID = "519beb85-e9a9-43a3-a753-16ed36d4de48"  # fixture operation of WORK_ID


def classification(**overrides) -> DefectClassification:
    data = {"description": "Коронка не садится.", "defect_type": "fit", "severity": "medium", "confidence": "high"}
    return DefectClassification(**{**data, **overrides})


def redo_decision() -> RedoDecision:
    return RedoDecision(
        proposal=RedoProposal(operation_number=1, likely_cause="Малый зазор.", recommendation="Увеличить зазор."),
        operation=Operation.objects.get(id=RESET_OPERATION_ID),
    )


class GraphTestBase(BaseTestCase):
    def setUp(self):
        from accounts.models import User

        self.work = Work.objects.get(id=WORK_ID)
        self.triage = DefectTriage.objects.create(order_id=ORDER_ID, comment="Коронка не садится")
        self.triage.works.add(self.work)
        self.config = {"configurable": {"thread_id": self.triage.thread_id}}
        self.admin_id = str(User.objects.get(email=self.admin_email).id)

    def build(self):
        return build_graph(InMemorySaver())

    def start(self, classify_result=None, precedents=None, propose_results=None):
        """Run the graph until the review interrupt, with the LLM/retrieval mocked at the graph module."""
        patches = [
            patch("defects.graph.classify_defect", return_value=classify_result or classification()),
            patch("defects.graph.get_precedents", return_value=precedents if precedents is not None else ["Прецедент"]),
            patch("defects.graph.propose_redo", side_effect=propose_results or [redo_decision()]),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.graph = self.build()
        return self.graph.invoke({"triage_id": str(self.triage.id)}, config=self.config)

    def resume(self, decision: dict):
        if not hasattr(self, "graph"):
            self.graph = self.build()
        return self.graph.invoke(Command(resume=decision), config=self.config)

    def approve(self, **final) -> dict:
        decision = {"action": "approve", "note": "", "decided_by_id": self.admin_id}
        if final:
            decision["final"] = final
        return decision

    def state_after_pause(self):
        snapshot = self.graph.get_state(self.config)
        return snapshot.values, snapshot.next


class HappyPathGraphTest(GraphTestBase):
    def test_runs_to_review_interrupt_and_applies_on_approve(self):
        self.start()
        values, next_nodes = self.state_after_pause()

        self.assertEqual(next_nodes, ("review",))  # paused at the human gate
        self.assertEqual(values["proposal"]["operation_id"], RESET_OPERATION_ID)
        self.assertEqual(values["precedents"], ["Прецедент"])
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.AWAITING_REVIEW)
        self.assertEqual(triage.proposal["operation_id"], RESET_OPERATION_ID)

        final = {"operation_id": RESET_OPERATION_ID, "likely_cause": "Малый зазор.", "recommendation": "Увеличить зазор."}
        with patch("defects.graph.add_case") as add_case:
            result = self.resume(self.approve(**final))

        self.assertIn("notified", result)
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(triage.decision, DefectTriage.Decision.APPROVE)
        self.assertEqual(triage.final["operation_id"], RESET_OPERATION_ID)
        self.assertIsNotNone(triage.applied_at)
        self.assertIsNotNone(triage.notified_at)
        self.assertIsNotNone(triage.decided_at)

        operation = Operation.objects.get(id=RESET_OPERATION_ID)
        self.assertEqual(operation.operation_status.number, 1)  # back to the queue
        self.assertIsNone(operation.exec_start)
        self.assertTrue(operation.is_exec_start_editable)
        add_case.assert_called_once()

    def test_review_writes_nothing_while_paused(self):
        # review only interrupts; the decision is recorded by apply, so a pause must leave no half-decision behind
        self.start()
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.decision, "")
        self.assertIsNone(triage.decided_at)
        self.assertIsNone(triage.applied_at)

    def test_apply_is_idempotent(self):
        self.start()
        self.resume(self.approve(operation_id=RESET_OPERATION_ID))
        triage = DefectTriage.objects.get(id=self.triage.id)
        applied_at = triage.applied_at

        apply_node({"triage_id": str(self.triage.id), "decision": self.approve(operation_id=RESET_OPERATION_ID)})

        triage.refresh_from_db()
        self.assertEqual(triage.applied_at, applied_at)  # nothing was done twice
        self.assertEqual(Operation.objects.get(id=RESET_OPERATION_ID).operation_status.number, 1)

    def test_edit_applies_the_admin_values(self):
        self.start()
        other = Operation.objects.exclude(id=RESET_OPERATION_ID).filter(work__order_id=ORDER_ID).first()
        if other is None:  # the fixture order has only one operation with a work - create another one
            other = Operation.objects.create(
                work=self.work, operation_type=Operation.objects.first().operation_type, ordinal_number=7,
                operation_status=OperationStatus.get_default_status(),
            )
        result = self.resume({
            "action": "edit", "note": "фрезеровка, а не подготовка",
            "final": {"operation_id": str(other.id), "likely_cause": "Другая причина.", "recommendation": "Другое."},
            "decided_by_id": self.admin_id,
        })
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(triage.final["operation_id"], str(other.id))
        self.assertEqual(triage.decision_note, "фрезеровка, а не подготовка")
        self.assertEqual(Operation.objects.get(id=other.id).operation_status.number, 1)

    def test_dismiss_closes_without_changes(self):
        self.start()
        self.resume({"action": "dismiss", "note": "не дефект", "decided_by_id": self.admin_id})
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.REJECTED)
        self.assertEqual(triage.final, {})
        self.assertIsNone(triage.applied_at)
        operation = Operation.objects.get(id=RESET_OPERATION_ID)
        self.assertNotEqual(operation.operation_status.number, 1)


class RejectLoopGraphTest(GraphTestBase):
    def test_reject_returns_to_propose_with_feedback(self):
        self.start(propose_results=[redo_decision(), redo_decision()])
        self.resume({"action": "reject", "note": "причина в фрезеровке", "decided_by_id": self.admin_id})
        self.resume(self.approve(operation_id=RESET_OPERATION_ID))

        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.APPLIED)
        self.assertEqual(triage.revisions, 1)
        from defects.graph import propose_redo as mock
        second_call = mock.call_args_list[1].kwargs
        self.assertEqual(second_call["feedback"], "причина в фрезеровке")

    def test_reject_beyond_max_revisions_goes_manual(self):
        self.triage.revisions = MAX_REVISIONS  # the budget is spent: the next reject must not reach the LLM
        self.triage.save(update_fields=["revisions"])
        self.start(propose_results=[redo_decision()])

        self.resume({"action": "reject", "note": "снова не то", "decided_by_id": self.admin_id})
        values, next_nodes = self.state_after_pause()
        self.assertEqual(next_nodes, ("review",))
        self.assertTrue(values["manual"])
        self.assertIsNone(values.get("proposal"))
        self.assertIn("revision limit", values["error"])

        # manual review: the administrator supplies everything by hand
        self.resume({
            "action": "edit", "note": "",
            "final": {"operation_id": RESET_OPERATION_ID, "likely_cause": "Своя причина.", "recommendation": "Своё."},
            "decided_by_id": self.admin_id,
        })
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.APPLIED)


class ManualReviewGraphTest(GraphTestBase):
    def test_classification_failure_goes_manual(self):
        from llm.exceptions import LlmUnavailable
        patches = [
            patch("defects.graph.classify_defect", side_effect=LlmUnavailable("boom")),
            patch("defects.graph.get_precedents", return_value=[]),
            patch("defects.graph.propose_redo"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.graph = self.build()
        self.graph.invoke({"triage_id": str(self.triage.id)}, config=self.config)

        values, next_nodes = self.state_after_pause()
        self.assertEqual(next_nodes, ("review",))
        self.assertTrue(values["manual"])
        self.assertIn("classification failed", values["error"])
        self.assertIsNone(values.get("proposal"))
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.PROCESSING)

    def test_low_confidence_goes_manual(self):
        self.start(classify_result=classification(confidence="low"))
        values, _ = self.state_after_pause()
        self.assertTrue(values["manual"])
        self.assertEqual(values["classification"]["confidence"], "low")

    def test_retrieval_failure_goes_manual(self):
        with patch("defects.graph.classify_defect", return_value=classification()):
            with patch("defects.graph.get_precedents", side_effect=RuntimeError("embeddings down")):
                with patch("defects.graph.propose_redo"):
                    self.graph = self.build()
                    self.graph.invoke({"triage_id": str(self.triage.id)}, config=self.config)
        values, _ = self.state_after_pause()
        self.assertTrue(values["manual"])
        self.assertIn("precedent retrieval failed", values["error"])

    def test_manual_approve_without_operation_closes_as_rejected(self):
        self.start(classify_result=classification(confidence="low"))
        self.resume(self.approve())  # nothing to apply
        triage = DefectTriage.objects.get(id=self.triage.id)
        self.assertEqual(triage.state, DefectTriage.State.REJECTED)
        self.assertIsNone(triage.applied_at)


class NotifyNodeTest(GraphTestBase):
    def test_notify_stores_the_case_and_marks_notified(self):
        self.start()
        with patch("defects.graph.add_case") as add_case:
            self.resume(self.approve(
                operation_id=RESET_OPERATION_ID, likely_cause="Малый зазор.", recommendation="Увеличить зазор.",
            ))
        add_case.assert_called_once()
        kwargs = add_case.call_args.kwargs
        self.assertEqual(kwargs["cause"], "Малый зазор.")
        self.assertEqual(kwargs["resolution"], "Увеличить зазор.")
        self.assertEqual(kwargs["triage"].id, self.triage.id)
        self.assertIsNotNone(DefectTriage.objects.get(id=self.triage.id).notified_at)

    def test_notify_survives_embedding_failure(self):
        self.start()
        with patch("defects.graph.add_case", side_effect=RuntimeError("embedding endpoint down")):
            result = self.resume(self.approve(operation_id=RESET_OPERATION_ID))
        self.assertTrue(result["notified"])  # the workflow still finishes
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.APPLIED)


class PostgresCheckpointerTest(GraphTestBase):
    """Integration: the same workflow against the Postgres checkpointer used in production."""

    def test_graph_pauses_and_resumes_across_postgres_checkpoints(self):
        from langgraph.checkpoint.postgres import PostgresSaver

        db = settings.DATABASES["default"]
        dsn = (
            f"host={db['HOST'] or 'localhost'} port={db.get('PORT', 5432)} dbname={db['NAME']} "
            f"user={db['USER']} password={db['PASSWORD']}"
        )
        with PostgresSaver.from_conn_string(dsn) as checkpointer:
            checkpointer.setup()
            graph = build_graph(checkpointer)
            with (
                patch("defects.graph.classify_defect", return_value=classification()),
                patch("defects.graph.get_precedents", return_value=["Прецедент"]),
                patch("defects.graph.propose_redo", return_value=redo_decision()),
                patch("defects.graph.add_case"),
            ):
                graph.invoke({"triage_id": str(self.triage.id)}, config=self.config)  # pauses at review

                snapshot = graph.get_state(self.config)
                self.assertEqual(snapshot.next, ("review",))  # the pause survived in Postgres, not in memory

                result = graph.invoke(
                    Command(resume={"action": "approve", "note": "",
                                    "final": {"operation_id": RESET_OPERATION_ID}, "decided_by_id": self.admin_id}),
                    config=self.config,
                )
        self.assertTrue(result["notified"])
        self.assertEqual(DefectTriage.objects.get(id=self.triage.id).state, DefectTriage.State.APPLIED)
