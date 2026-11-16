"""
Where the system prompts of the triage workflow come from.

The texts live in files next to this module (prompt_templates/*.txt) and are always available. When
PROMPT_SOURCE=langsmith the provider pulls the version tagged PROMPT_TAG from the LangSmith prompt hub instead, so a
prompt can be edited, tested and rolled back without a deploy.
"""
import hashlib
import json
import logging
import re
import threading
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from django.conf import settings
from pydantic import ValidationError

from defects.models import DefectSeverity, DefectType
from defects.triage.schemas import DefectClassification, RedoProposal

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "prompt_templates"

CLASSIFY = "dental-lab-defect-classify"
PROPOSE = "dental-lab-defect-propose"

SOURCE_LOCAL = "local"
SOURCE_LANGSMITH = "langsmith"

HUB_CONNECT_TIMEOUT_MS = 3000
HUB_READ_TIMEOUT_MS = 5000


class PromptInvalid(ValueError):
    """A prompt text or manifest that the workflow must not use."""


@dataclass(frozen=True)
class PromptVersion:
    name: str
    text: str
    source: str  # SOURCE_LOCAL or SOURCE_LANGSMITH
    version: str  # LangSmith commit hash, or the first 12 hex digits of the sha256 of a local file

    @property
    def label(self) -> str:
        return f"{self.source}:{self.version}"

_ANSWER_LINE = re.compile(r"^Answer: (\{.*\})$", flags=re.MULTILINE)


def _examples(text: str) -> list[dict]:
    try:
        return [json.loads(raw) for raw in _ANSWER_LINE.findall(text)]
    except json.JSONDecodeError as exc:
        raise PromptInvalid(f"an example answer is not valid JSON: {exc}") from exc


def _check_contract(text: str, *, labels: tuple[str, ...], tag: str, schema: type, name: str) -> None:
    missing = [label for label in labels if label not in text]
    if missing:
        raise PromptInvalid(f"{name}: labels missing from the prompt: {', '.join(missing)}")
    if f"<{tag}>" not in text:
        raise PromptInvalid(f"{name}: the <{tag}> tag that the message builder relies on is missing")
    examples = _examples(text)
    if not examples:
        raise PromptInvalid(f"{name}: no worked example ('Answer: {{...}}' line)")
    for example in examples:
        try:
            schema(**example)
        except (ValidationError, TypeError) as exc:
            raise PromptInvalid(f"{name}: a worked example does not match its schema: {exc}") from exc


def _validate_classify(text: str) -> None:
    labels = (*DefectType.values, *DefectSeverity.values, "low", "medium", "high")
    _check_contract(text, labels=labels, tag="report", schema=DefectClassification, name=CLASSIFY)


def _validate_propose(text: str) -> None:
    _check_contract(text, labels=(), tag="feedback", schema=RedoProposal, name=PROPOSE)


_VALIDATORS: dict[str, Callable[[str], None]] = {CLASSIFY: _validate_classify, PROPOSE: _validate_propose}
_FILES = {CLASSIFY: "classify.system.txt", PROPOSE: "propose.system.txt"}
PROMPT_NAMES = tuple(_FILES)


def validate_prompt_text(name: str, text: str) -> None:
    """Raise PromptInvalid unless `text` fits the code that uses it: labels, tags and worked examples."""
    if name not in _VALIDATORS:
        raise KeyError(f"unknown prompt {name!r}")
    _VALIDATORS[name](text)


def local_prompt(name: str) -> PromptVersion:
    text = (TEMPLATES_DIR / _FILES[name]).read_text(encoding="utf-8").strip()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return PromptVersion(name=name, text=text, source=SOURCE_LOCAL, version=digest)


def extract_system_text(manifest: dict[str, Any]) -> str:
    """The text of a prompt that consists of one system message without variables, taken from the raw manifest."""
    try:
        kwargs = manifest["kwargs"]
        messages = kwargs["messages"]
        if kwargs.get("input_variables"):
            raise PromptInvalid(f"the prompt has variables: {kwargs['input_variables']}")
        if len(messages) != 1 or messages[0]["id"][-1] != "SystemMessagePromptTemplate":
            raise PromptInvalid("the prompt must consist of exactly one system message")
        template = messages[0]["kwargs"]["prompt"]["kwargs"]
        if template.get("input_variables"):
            raise PromptInvalid(f"the prompt has variables: {template['input_variables']}")
        text = template["template"]
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise PromptInvalid(f"unexpected prompt manifest structure: {exc!r}") from exc
    if not isinstance(text, str) or not text.strip():
        raise PromptInvalid("the prompt text is empty")
    return text.strip()


def make_template(text: str):
    """The LangChain object LangSmith stores for a one-message prompt. Mustache keeps JSON braces literal."""
    from langchain_core.prompts import ChatPromptTemplate

    return ChatPromptTemplate.from_messages([("system", text)], template_format="mustache")


@lru_cache(maxsize=1)
def get_client():
    from langsmith import Client
    from urllib3.util import Retry

    return Client(
        timeout_ms=(HUB_CONNECT_TIMEOUT_MS, HUB_READ_TIMEOUT_MS),
        retry_config=Retry(total=1, backoff_factor=0.2),
    )


def _pull(name: str) -> PromptVersion:
    commit = get_client().pull_prompt_commit(f"{name}:{settings.PROMPT_TAG}", skip_cache=True)
    text = extract_system_text(commit.manifest)
    validate_prompt_text(name, text)
    return PromptVersion(name=name, text=text, source=SOURCE_LANGSMITH, version=commit.commit_hash)


@dataclass
class _Entry:
    prompt: PromptVersion
    expires_at: float


_cache: dict[str, _Entry] = {}
_lock = threading.Lock()


def clear_cache() -> None:
    with _lock:
        _cache.clear()
    get_client.cache_clear()


def get_prompt(name: str) -> PromptVersion:
    """The prompt to use right now. Never raises because of LangSmith."""
    if name not in _FILES:
        raise KeyError(f"unknown prompt {name!r}")
    if settings.PROMPT_SOURCE != SOURCE_LANGSMITH:
        return local_prompt(name)

    with _lock:
        now = time.monotonic()
        entry = _cache.get(name)
        if entry and now < entry.expires_at:
            return entry.prompt
        try:
            prompt = _pull(name)
        except Exception as exc:  # network, auth, 404, invalid edit: the workflow must keep running
            fallback = entry.prompt if entry else local_prompt(name)
            logger.warning(
                "prompt %s:%s unavailable from LangSmith (%s: %s); using %s for the next %.0fs",
                name, settings.PROMPT_TAG, type(exc).__name__, str(exc)[:200], fallback.label,
                settings.PROMPT_FAILURE_BACKOFF_S,
            )
            _cache[name] = _Entry(fallback, now + settings.PROMPT_FAILURE_BACKOFF_S)
            return fallback
        _cache[name] = _Entry(prompt, now + settings.PROMPT_CACHE_TTL_S)
        return prompt
