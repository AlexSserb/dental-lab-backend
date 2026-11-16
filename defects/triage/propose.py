"""Step 2 of the triage workflow: pick the operation that must be redone and name the likely cause."""
from dataclasses import dataclass

from llm.service import call_structured
from operations.models import Operation

from defects.triage.case_service import get_precedents
from defects.triage.prompt_provider import PROPOSE, get_prompt
from defects.triage.prompts import build_propose_message
from defects.triage.schemas import RedoProposal

FEATURE = "defect_propose"


@dataclass(frozen=True)
class RedoDecision:
    # `operation_number` is the model's pick from the list; `operation` is the real row behind it, mapped by us.
    proposal: RedoProposal
    operation: Operation


@dataclass(frozen=True)
class Candidate:
    operation: Operation
    line: str  # display line of the shape "Проектирование коронки (Циркониевая коронка)"


def propose_redo(
    works, description: str, defect_type: str, severity: str, feedback: str = "",
    precedents: list[str] | None = None, user=None,
) -> RedoDecision:
    """
    Propose which production operation caused the defect and must be repeated. The candidates are the operations
    of the reported works, loaded from the DB: the model only picks a number from the list, and the validator
    rejects any number outside it (same trick as work_type_number in order drafting) - we map the number back to
    an Operation id ourselves, so nothing outside the real operations can be proposed. `feedback` is the
    administrator's comment from a rejected proposal; like the doctor's comment it is untrusted text and the
    prompt keeps it inside <feedback></feedback> tags. `precedents` lets a caller that has already run retrieval
    pass the texts in instead of fetching them again. `user` goes into the LLM call log.
    """
    candidates = _candidates(works)

    def check(proposal: RedoProposal) -> None:
        if not (1 <= proposal.operation_number <= len(candidates)):
            raise ValueError(
                f"operation_number {proposal.operation_number} is not in the list (valid: 1-{len(candidates)})"
            )

    proposal = call_structured(
        feature=FEATURE,
        system=get_prompt(PROPOSE).text,
        user_text=build_propose_message(
            description, defect_type, severity,
            [candidate.line for candidate in candidates],
            precedents if precedents is not None else get_precedents(description),
            feedback,
        ),
        schema=RedoProposal,
        validator=check,
        user=user,
    )
    return RedoDecision(proposal=proposal, operation=candidates[proposal.operation_number - 1].operation)


def _candidates(works) -> list[Candidate]:
    """Operations of the reported works in production order (work by work, ordinal inside the work)."""
    rows = (
        Operation.objects.filter(work__in=works)
        .select_related("operation_type", "work", "work__work_type")
        .order_by("work_id", "ordinal_number")
    )
    return [
        Candidate(operation=operation, line=f"{operation.operation_type.name} ({operation.work.work_type.name})")
        for operation in rows
    ]
