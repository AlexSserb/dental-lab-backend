import logging
import time
from decimal import Decimal
from typing import Callable, TypeVar

import openai
from django.conf import settings
from pydantic import BaseModel, ValidationError

from .client import get_client
from .exceptions import LlmError, LlmNotConfigured, LlmUnavailable, LlmValidationFailed
from .models import LlmCallLog

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> Decimal:
    per_m = Decimal(1_000_000)
    return (
        Decimal(prompt_tokens) * Decimal(settings.AI_PRICE_INPUT_PER_1M)
        + Decimal(completion_tokens) * Decimal(settings.AI_PRICE_OUTPUT_PER_1M)
    ) / per_m


def call_structured(
    *,
    feature: str,
    system: str,
    user_text: str,
    schema: type[T],
    validator: Callable[[T], None] | None = None,
    user=None,
) -> T:
    """Ask the model for output matching a Pydantic `schema`."""
    client = get_client()
    max_attempts = settings.AI_MAX_RETRIES + 1
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user_text}]

    prompt_tokens = completion_tokens = attempts = 0
    started = time.monotonic()
    error = ""
    result: T | None = None

    try:
        while attempts < max_attempts:
            attempts += 1
            try:
                completion = client.chat.completions.parse(
                    model=settings.AI_MODEL,
                    messages=messages,
                    response_format=schema,
                    temperature=0,
                )
            except (openai.APIConnectionError, openai.APITimeoutError, openai.APIStatusError) as exc:
                raise LlmUnavailable(f"{type(exc).__name__}: {exc}") from exc
            except ValidationError as exc:  # SDK parses content into `schema` itself
                error = _short(exc)
                _append_feedback(messages, "", error)
                continue
            except openai.LengthFinishReasonError as exc:
                raise LlmUnavailable("Model output was cut off (token limit / context too small)") from exc

            if completion.usage:
                prompt_tokens += completion.usage.prompt_tokens
                completion_tokens += completion.usage.completion_tokens
                _warn_if_context_nearly_full(feature, completion.usage.prompt_tokens)

            message = completion.choices[0].message
            if message.refusal or message.parsed is None:
                error = message.refusal or "Empty or unparsable response"
                _append_feedback(messages, message.content or "", error)
                continue

            try:
                if validator:
                    validator(message.parsed)
            except ValueError as exc:
                error = _short(exc)
                _append_feedback(messages, message.content or "", error)
                continue

            result = message.parsed
            error = ""
            break

        if result is None:
            raise LlmValidationFailed(f"No valid output after {attempts} attempt(s): {error}")
        return result
    except LlmError as exc:
        error = str(exc)
        raise
    finally:
        _record_call(feature, user, started, prompt_tokens, completion_tokens, attempts, result is not None, error)


def call_text(*, feature: str, system: str, user_text: str, user=None) -> str:
    """Ask the model for a free-text answer (no schema, no retries beyond the SDK's transport retries)."""
    client = get_client()
    started = time.monotonic()
    prompt_tokens = completion_tokens = 0
    error = ""
    answer: str | None = None

    try:
        try:
            completion = client.chat.completions.create(
                model=settings.AI_MODEL,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user_text}],
                temperature=0,
            )
        except (openai.APIConnectionError, openai.APITimeoutError, openai.APIStatusError) as exc:
            raise LlmUnavailable(f"{type(exc).__name__}: {exc}") from exc

        if completion.usage:
            prompt_tokens = completion.usage.prompt_tokens
            completion_tokens = completion.usage.completion_tokens
            _warn_if_context_nearly_full(feature, prompt_tokens)

        answer = (completion.choices[0].message.content or "").strip()
        if not answer:
            raise LlmUnavailable("Empty response from the model")
        return answer
    except LlmError as exc:
        error = str(exc)
        raise
    finally:
        _record_call(feature, user, started, prompt_tokens, completion_tokens, 1, answer is not None, error)


def _record_call(feature, user, started, prompt_tokens, completion_tokens, attempts, success, error) -> None:
    latency = time.monotonic() - started
    cost = estimate_cost(prompt_tokens, completion_tokens)
    try:
        LlmCallLog.objects.create(
            feature=feature, model=settings.AI_MODEL, user=user if getattr(user, "pk", None) else None,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, attempts=attempts,
            latency=round(latency, 3), cost=cost, success=success, error=error[:512],
        )
    except Exception:
        logger.exception("Failed to write LlmCallLog")
    logger.info("llm feature=%s model=%s attempts=%s latency=%.2fs tokens=%s+%s cost=$%s ok=%s",
                feature, settings.AI_MODEL, attempts, latency, prompt_tokens, completion_tokens, cost, success)


def _warn_if_context_nearly_full(feature: str, prompt_tokens: int) -> None:
    limit = settings.AI_CONTEXT_TOKENS
    if limit and prompt_tokens > 0.8 * limit:
        logger.warning("llm feature=%s prompt uses %s of %s context tokens; the provider may truncate it",
                       feature, prompt_tokens, limit)


def _append_feedback(messages: list[dict], previous: str, error: str) -> None:
    if previous:
        messages.append({"role": "assistant", "content": previous})
    messages.append({
        "role": "user",
        "content": f"Your previous answer was invalid: {error}\nFix these problems and answer again.",
    })


def _short(exc: Exception) -> str:
    return " ".join(str(exc).split())[:500]


__all__ = ["call_structured", "estimate_cost", "LlmError", "LlmNotConfigured", "LlmUnavailable",
           "LlmValidationFailed", "call_text"]
