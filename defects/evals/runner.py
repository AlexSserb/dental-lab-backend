"""
The eval harness for the defect triage prompts: labeled cases in triage_cases.json are run through the same
classify_defect / propose machinery the workflow uses (same prompts, same schemas, same retries), and the
answers are scored against the labels. Runs against a real LLM - it is never used in tests.
"""
import json
import logging
import time
from pathlib import Path

from django.conf import settings

from defects.triage.classify import classify_defect
from defects.triage.prompt_provider import PROPOSE, get_prompt
from defects.triage.prompts import build_propose_message
from defects.triage.schemas import RedoProposal
from llm.service import call_structured

logger = logging.getLogger(__name__)

CASES_PATH = Path(__file__).with_name("triage_cases.json")

# The propose step of the eval is scored in isolation from classification: the labeled type and severity go
# into the prompt, so operation-choice accuracy does not absorb classification mistakes.
PROPOSE_EVAL_FEATURE = "defect_propose_eval"


def load_cases() -> list[dict]:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]
    for case in cases:
        assert 1 <= case["expected_operation"] <= len(case["operations"]), f"{case['id']}: label out of range"
    return cases


def run_eval(cases: list[dict], report=print) -> dict:
    """
    Run every case through classification and operation choice, score against the labels and return the totals.
    `report` receives one progress line per case. A case whose LLM call ultimately fails counts as a miss
    for both metrics - a workflow that cannot get an answer is wrong, not exempt.
    With LangSmith tracing on, the whole eval becomes one parent run ("eval_triage") with every case nested
    under it, so model runs are comparable in the LangSmith UI.
    """
    type_hits = severity_hits = both_hits = operation_hits = 0
    failures: list[dict] = []
    started = time.monotonic()

    with _eval_trace(cases):
        for index, case in enumerate(cases, start=1):
            line = f"[{index}/{len(cases)}] {case['id']}: "
            try:
                classification = classify_defect(case["work_names"], case["comment"])
                line += f"type={classification.defect_type} severity={classification.severity}"
                type_ok = classification.defect_type == case["defect_type"]
                severity_ok = classification.severity == case["severity"]
                type_hits += type_ok
                severity_hits += severity_ok
                both_hits += type_ok and severity_ok
                line += " ok" if type_ok and severity_ok else " miss"
            except Exception as exc:
                classification = None
                type_ok = severity_ok = False
                line += f" classification failed: {exc}"

            try:
                number = propose_number(case)
                operation_ok = number == case["expected_operation"]
                operation_hits += operation_ok
                line += f", op={number}" + ("" if operation_ok else f" (expected {case['expected_operation']})")
            except Exception as exc:
                operation_ok = False
                line += f", operation choice failed: {exc}"

            if not (type_ok and severity_ok and operation_ok):
                failures.append({"id": case["id"], "type_ok": type_ok, "severity_ok": severity_ok,
                                 "operation_ok": operation_ok})
            report(line)

    total = len(cases)
    return {
        "total": total,
        "elapsed_s": round(time.monotonic() - started, 1),
        "defect_type": type_hits,
        "severity": severity_hits,
        "classification_both": both_hits,
        "operation": operation_hits,
        "failures": failures,
    }


def _eval_trace(cases: list[dict]):
    """One parent LangSmith run for the whole eval (no-op when tracing is off)."""
    if not settings.LANGSMITH_TRACING:
        from contextlib import nullcontext
        return nullcontext()
    from langsmith import trace
    return trace(
        name="eval_triage",
        metadata={"model": settings.AI_MODEL, "cases": len(cases)},
        tags=["eval", "triage"],
    )


def propose_number(case: dict) -> int:
    """The propose step of the eval: same prompt and schema as propose_redo, without touching the database."""
    proposal = call_structured(
        feature=PROPOSE_EVAL_FEATURE,
        system=get_prompt(PROPOSE).text,
        user_text=build_propose_message(
            case["comment"], case["defect_type"], case["severity"],
            case["operations"],
            [],  # no precedents: the metric must not depend on what happens to be in the case store
        ),
        schema=RedoProposal,
        validator=lambda p: _check_range(p, len(case["operations"])),
    )
    return proposal.operation_number


def _check_range(proposal: RedoProposal, count: int) -> None:
    if not (1 <= proposal.operation_number <= count):
        raise ValueError(f"operation_number {proposal.operation_number} is not in the list (valid: 1-{count})")


def format_report(model: str, results: dict) -> str:
    total = results["total"]
    percent = lambda hits: f"{hits}/{total} ({hits / total:.0%})"  # noqa: E731
    lines = [
        f"Model: {model}",
        f"Cases: {total}, elapsed {results['elapsed_s']}s",
        "Classification accuracy:",
        f"  defect type:        {percent(results['defect_type'])}",
        f"  severity:           {percent(results['severity'])}",
        f"  both correct:       {percent(results['classification_both'])}",
        f"Operation choice:    {percent(results['operation'])}",
    ]
    if results["failures"]:
        lines.append("Misses:")
        for failure in results["failures"]:
            missed = [name for name, ok in
                      (("type", failure["type_ok"]), ("severity", failure["severity_ok"]),
                       ("operation", failure["operation_ok"])) if not ok]
            lines.append(f"  {failure['id']}: {', '.join(missed)}")
    return "\n".join(lines)
