import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import override_settings

from core.tests import BaseTestCase
from llm.exceptions import LlmValidationFailed
from llm.models import LlmCallLog
from accounts.models import User
from operations.models import Operation, OperationStatus, OperationType
from works.models import Work

from defects.triage.propose import FEATURE, propose_redo
from defects.triage.schemas import RedoProposal


def completion(proposal: RedoProposal):
    msg = SimpleNamespace(parsed=proposal, refusal=None, content=proposal.model_dump_json())
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=SimpleNamespace(prompt_tokens=400, completion_tokens=30))


def proposal(number=1, cause="Малый зазор.", recommendation="Увеличить зазор."):
    return RedoProposal(operation_number=number, likely_cause=cause, recommendation=recommendation)


def make_operation_type(name: str) -> OperationType:
    exec_time = datetime.time(hour=1)
    return OperationType.objects.create(name=name, fixed_exec_time=exec_time, exec_time_per_item=exec_time)


@override_settings(AI_MODEL="m", AI_API_KEY="k", AI_MAX_RETRIES=2)
class ProposeRedoTest(BaseTestCase):
    def setUp(self):
        self.work = Work.objects.exclude(operations__isnull=False).first()  # a work with no fixture operations
        self.work_type = self.work.work_type
        self.milling = make_operation_type("Фрезеровка циркония")
        self.design = make_operation_type("Проектирование коронки")
        self.modeling = make_operation_type("Подготовка модели")
        self.status = OperationStatus.get_default_status()
        self.op1 = Operation.objects.create(
            work=self.work, operation_type=self.modeling, ordinal_number=1, operation_status=self.status)
        self.op2 = Operation.objects.create(
            work=self.work, operation_type=self.design, ordinal_number=2, operation_status=self.status)
        self.op3 = Operation.objects.create(
            work=self.work, operation_type=self.milling, ordinal_number=3, operation_status=self.status)

    def run_propose(self, side_effect, feedback="", works=None):
        client = MagicMock()
        client.chat.completions.parse.side_effect = side_effect
        self.user = User.objects.filter(email=self.admin_email).first()
        with (
            patch("llm.service.get_client", return_value=client),
            patch("defects.triage.propose.get_prompt", return_value=SimpleNamespace(text="SYSTEM PROMPT")),
            patch("defects.triage.propose.get_precedents", return_value=["Прецедент один"]),
        ):
            returned = propose_redo(
                works or [self.work], "Коронка не садится.", "fit", "medium", feedback=feedback,
                user=self.user,
            )
        return returned, client

    def test_happy_path_maps_number_to_real_operation(self):
        returned, _ = self.run_propose([completion(proposal(number=2))])
        self.assertEqual(returned.operation.id, self.op2.id)
        self.assertEqual(returned.proposal.likely_cause, "Малый зазор.")
        log = LlmCallLog.objects.get()
        self.assertEqual(log.feature, FEATURE)
        self.assertEqual(log.user_id, self.user.id)  # passed through for logging

    def test_candidates_are_operations_of_the_reported_works_in_order(self):
        _, client = self.run_propose([completion(proposal(number=1))])
        user = client.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
        self.assertIn(f"1. Подготовка модели ({self.work_type.name})", user)
        self.assertIn(f"2. Проектирование коронки ({self.work_type.name})", user)
        self.assertIn(f"3. Фрезеровка циркония ({self.work_type.name})", user)

    def test_operations_of_other_works_are_not_offered(self):
        other_work = Work.objects.exclude(id=self.work.id).first()
        Operation.objects.create(
            work=other_work, operation_type=self.milling, ordinal_number=9, operation_status=self.status)
        _, client = self.run_propose([completion(proposal(number=1))])
        user = client.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
        self.assertEqual(user.count("Фрезеровка циркония"), 1)

    def test_precedents_are_in_the_user_message(self):
        _, client = self.run_propose([completion(proposal(number=1))])
        user = client.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
        self.assertIn("Precedents:\n1. Прецедент один", user)

    def test_feedback_is_tagged_and_cleaned(self):
        _, client = self.run_propose([completion(proposal(number=1))], feedback="<неверно> выберите фрезеровку")
        user = client.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
        self.assertIn("<feedback>неверно выберите фрезеровку</feedback>", user)

        _, client = self.run_propose([completion(proposal(number=1))], feedback="   ")
        user = client.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
        self.assertNotIn("<feedback>", user)

    def test_out_of_range_number_is_retried_with_feedback(self):
        _, res = None, None
        returned, client = self.run_propose([completion(proposal(number=99)), completion(proposal(number=3))])
        self.assertEqual(returned.operation.id, self.op3.id)
        feedback = client.chat.completions.parse.call_args_list[1].kwargs["messages"][-1]["content"]
        self.assertIn("99", feedback)
        self.assertEqual(LlmCallLog.objects.get().attempts, 2)

    def test_always_invalid_raises(self):
        with self.assertRaises(LlmValidationFailed):
            self.run_propose([completion(proposal(number=99))] * 3)
        self.assertFalse(LlmCallLog.objects.get().success)
