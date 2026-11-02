import logging
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import override_settings
from pydantic import ValidationError

from core.tests import BaseTestCase
from llm.models import LlmCallLog
from orders.drafting.schemas import DraftWork, OrderDraft
from orders.models import Order
from works.models import WorkType


def completion(draft: OrderDraft):
    msg = SimpleNamespace(parsed=draft, refusal=None, content=draft.model_dump_json())
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=SimpleNamespace(prompt_tokens=500, completion_tokens=40))


def draft(number=1, teeth=(21, 22), amount=2, color="A2", days=10):
    return OrderDraft(works=[DraftWork(work_type_number=number, teeth=list(teeth), amount=amount)],
                      tooth_color=color, days_from_now=days, comment=None)


class DraftSchemaTest(BaseTestCase):
    def test_rejects_invalid_teeth(self):
        for bad in ([51], [19], [49], [10], [0]):
            with self.assertRaises(ValidationError, msg=bad):
                DraftWork(work_type_number=1, teeth=bad, amount=1)

    def test_rejects_unknown_color_and_bad_deadline(self):
        with self.assertRaises(ValidationError):
            OrderDraft(works=[], tooth_color="A5", days_from_now=None, comment=None)
        with self.assertRaises(ValidationError):
            OrderDraft(works=[], tooth_color=None, days_from_now=0, comment=None)

    def test_teeth_deduplicated_and_sorted(self):
        self.assertEqual(DraftWork(work_type_number=1, teeth=[22, 21, 21], amount=2).teeth, [21, 22])


@override_settings(AI_MODEL="m", AI_API_KEY="k", AI_MAX_RETRIES=2)
class DraftFromTextTest(BaseTestCase):
    url = "/api/orders/draft-from-text/"

    def setUp(self):
        cache.clear()  # throttle counters live in the cache
        self.set_up_for_physician()
        self.work_types = list(WorkType.objects.order_by("name"))

    def post(self, side_effect, text="Циркониевая коронка на 21 и 22, цвет A2, нужно через 10 дней"):
        client = MagicMock()
        client.chat.completions.parse.side_effect = side_effect
        with patch("llm.service.get_client", return_value=client):
            return client, self.client.post(self.url, {"text": text}, format="json")

    def test_happy_path_maps_number_to_real_work_type(self):
        _, res = self.post([completion(draft(number=2))])
        self.assertEqual(res.status_code, 200)
        data = res.json()
        work = data["works"][0]
        self.assertEqual(work["workTypeId"], str(self.work_types[1].id))
        self.assertEqual(work["workTypeName"], self.work_types[1].name)
        self.assertEqual(work["teeth"], [21, 22])
        self.assertEqual(data["toothColor"], "A2")
        self.assertEqual(data["deadline"], (date.today() + timedelta(days=10)).isoformat())
        self.assertEqual(data["warnings"], [])
        self.assertEqual(LlmCallLog.objects.get().feature, "order_draft")

    def test_prompt_contains_real_work_types_in_user_message(self):
        client, _ = self.post([completion(draft())])
        system, user = client.chat.completions.parse.call_args.kwargs["messages"][:2]
        for wt in self.work_types:
            self.assertIn(wt.name, user["content"])
            self.assertNotIn(wt.name, system["content"])  # system prompt must stay static to be cacheable
        self.assertIn("Request: Циркониевая коронка", user["content"])

    def test_system_prompt_identical_for_different_requests(self):
        c1, _ = self.post([completion(draft())], text="коронка на 11")
        c2, _ = self.post([completion(draft())], text="мост на 34-36")
        first = c1.chat.completions.parse.call_args.kwargs["messages"][0]
        second = c2.chat.completions.parse.call_args.kwargs["messages"][0]
        self.assertEqual(first, second)

    def test_inactive_work_types_are_not_offered(self):
        hidden = self.work_types[0]
        WorkType.objects.filter(id=hidden.id).update(is_active=False)
        client, _ = self.post([completion(draft())])
        user = client.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
        self.assertNotIn(hidden.name, user)

    @override_settings(AI_MAX_CANDIDATES=5)
    def test_large_catalog_is_narrowed_and_numbers_map_to_candidates(self):
        for i in range(30):
            WorkType.objects.create(name=f"Вкладка тип {i:02d}")
        zirconia = WorkType.objects.create(name="Циркониевая коронка эстетическая")

        client, res = self.post([completion(draft(number=1))])  # candidates are sorted by name
        user = client.chat.completions.parse.call_args.kwargs["messages"][1]["content"]
        listed = [line for line in user.split("\n") if line[:2].rstrip(".").isdigit()]
        self.assertEqual(len(listed), 5)
        self.assertIn("Циркониевая коронка эстетическая", user)  # matched lexically
        names = [line.split(". ", 1)[1] for line in listed]
        self.assertEqual(res.json()["works"][0]["workTypeName"], names[0])
        self.assertIn(zirconia.name, names)

    @override_settings(AI_CONTEXT_TOKENS=600)
    def test_warns_when_prompt_nearly_fills_context(self):
        # manage.py calls logging.disable(CRITICAL) for `test`; lift it for this assertion
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, logging.CRITICAL)
        with self.assertLogs("llm.service", level="WARNING") as logs:
            self.post([completion(draft())])  # 500 prompt tokens > 80% of 600
        self.assertIn("context", logs.output[0])

    def test_out_of_range_number_is_retried_with_feedback(self):
        client, res = self.post([completion(draft(number=99)), completion(draft(number=1))])
        self.assertEqual(res.status_code, 200)
        feedback = client.chat.completions.parse.call_args_list[1].kwargs["messages"][-1]["content"]
        self.assertIn("99", feedback)
        self.assertEqual(LlmCallLog.objects.get().attempts, 2)

    def test_always_invalid_returns_422(self):
        _, res = self.post([completion(draft(number=99))] * 3)
        self.assertEqual(res.status_code, 422)
        self.assertFalse(LlmCallLog.objects.get().success)

    def test_warnings(self):
        empty = OrderDraft(works=[], tooth_color=None, days_from_now=None, comment=None)
        _, res = self.post([completion(empty)])
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()["warnings"]), 2)
        self.assertIsNone(res.json()["deadline"])

        _, res = self.post([completion(draft(amount=3))])
        self.assertIn("не совпадает", res.json()["warnings"][0])

    @override_settings(AI_MODEL="")
    def test_not_configured_returns_503(self):
        from llm.client import get_client
        get_client.cache_clear()
        res = self.client.post(self.url, {"text": "коронка"}, format="json")
        self.assertEqual(res.status_code, 503)

    def test_validation_and_auth(self):
        self.assertEqual(self.client.post(self.url, {"text": ""}, format="json").status_code, 400)
        self.assertEqual(self.client.post(self.url, {"text": "x" * 1001}, format="json").status_code, 400)
        self.client.credentials()
        self.assertEqual(self.client.post(self.url, {"text": "коронка"}, format="json").status_code, 401)

    def test_throttled_after_limit(self):
        for _ in range(20):
            self.assertEqual(self.post([completion(draft())])[1].status_code, 200)
        self.assertEqual(self.post([completion(draft())])[1].status_code, 429)


class CreateOrderDeadlineTest(BaseTestCase):
    url = "/api/orders/create-order/"

    def payload(self, **extra):
        return {
            "customer_id": "a2203146-68ba-411f-ba45-815a52ef7236", "tooth_color": "A2",
            "work_types": [{"work_type_id": "00be8d3f-a127-4de3-a1b7-1c5d093c2ae7", "amount": 1, "teeth": [11]}],
            **extra,
        }

    def test_explicit_deadline_is_used(self):
        self.set_up_for_physician()
        target = date.today() + timedelta(days=12)
        res = self.client.post(self.url, self.payload(deadline=target.isoformat()), format="json")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Order.objects.get(id=res.json()["orderId"]).deadline, target)

    def test_default_deadline_when_omitted(self):
        self.set_up_for_physician()
        res = self.client.post(self.url, self.payload(), format="json")
        self.assertEqual(Order.objects.get(id=res.json()["orderId"]).deadline, date.today() + timedelta(days=5))

    def test_past_deadline_rejected(self):
        self.set_up_for_physician()
        past = (date.today() - timedelta(days=1)).isoformat()
        self.assertEqual(self.client.post(self.url, self.payload(deadline=past), format="json").status_code, 400)
