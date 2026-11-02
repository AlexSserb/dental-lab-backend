from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from pydantic import BaseModel, field_validator

from .exceptions import LlmNotConfigured, LlmUnavailable, LlmValidationFailed
from .models import LlmCallLog
from .service import call_structured, estimate_cost


class Draft(BaseModel):
    teeth: list[int]

    @field_validator("teeth")
    @classmethod
    def teeth_range(cls, v):
        if any(t < 11 or t > 48 for t in v):
            raise ValueError("teeth must be 11-48")
        return v


def _completion(parsed, prompt=100, completion=20):
    msg = SimpleNamespace(parsed=parsed, refusal=None, content="{}")
    return SimpleNamespace(choices=[SimpleNamespace(message=msg)],
                           usage=SimpleNamespace(prompt_tokens=prompt, completion_tokens=completion))


@override_settings(AI_MODEL="m", AI_API_KEY="k", AI_MAX_RETRIES=2,
                   AI_PRICE_INPUT_PER_1M="1", AI_PRICE_OUTPUT_PER_1M="2")
class CallStructuredTest(TestCase):
    def _run(self, side_effect, validator=None):
        client = MagicMock()
        client.chat.completions.parse.side_effect = side_effect
        with patch("llm.service.get_client", return_value=client):
            return client, call_structured(feature="t", system="s", user_text="u", schema=Draft, validator=validator)

    def test_success_is_logged(self):
        _, res = self._run([_completion(Draft(teeth=[21, 22]))])
        self.assertEqual(res.teeth, [21, 22])
        log = LlmCallLog.objects.get()
        self.assertTrue(log.success)
        self.assertEqual((log.attempts, log.tokens), (1, 120))
        self.assertEqual(log.cost, Decimal("0.000140"))

    def test_business_validator_retries_with_feedback(self):
        def must_have_21(d):
            if 21 not in d.teeth:
                raise ValueError("tooth 21 missing")

        client, res = self._run([_completion(Draft(teeth=[11])), _completion(Draft(teeth=[21]))], must_have_21)
        self.assertEqual(res.teeth, [21])
        second_call_messages = client.chat.completions.parse.call_args_list[1].kwargs["messages"]
        self.assertIn("tooth 21 missing", second_call_messages[-1]["content"])
        log = LlmCallLog.objects.get()
        self.assertEqual(log.attempts, 2)
        self.assertTrue(log.success)

    def test_retries_exhausted(self):
        def never(_):
            raise ValueError("bad")

        with self.assertRaises(LlmValidationFailed):
            self._run([_completion(Draft(teeth=[21]))] * 3, never)
        log = LlmCallLog.objects.get()
        self.assertFalse(log.success)
        self.assertEqual(log.attempts, 3)

    def test_provider_error_is_wrapped(self):
        import openai

        exc = openai.APIConnectionError(request=MagicMock())
        with self.assertRaises(LlmUnavailable):
            self._run(exc)
        self.assertFalse(LlmCallLog.objects.get().success)

    @override_settings(AI_MODEL="")
    def test_not_configured(self):
        from .client import get_client
        get_client.cache_clear()
        with self.assertRaises(LlmNotConfigured):
            call_structured(feature="t", system="s", user_text="u", schema=Draft)

    def test_estimate_cost(self):
        self.assertEqual(estimate_cost(1_000_000, 1_000_000), Decimal(3))
