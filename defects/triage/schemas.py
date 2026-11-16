"""Pydantic models describing what the LLM must return in the defect triage workflow."""
from typing import Literal

from pydantic import BaseModel, field_validator

from defects.models import DefectSeverity, DefectType

# Literal puts the allowed values into the JSON schema, so the model cannot invent a defect type.
DefectTypeLiteral = Literal[tuple(DefectType.values)]  # type: ignore[valid-type]
SeverityLiteral = Literal[tuple(DefectSeverity.values)]  # type: ignore[valid-type]
# Small models give meaningless floats like 0.87; three levels are easier to produce and to threshold.
ConfidenceLiteral = Literal["low", "medium", "high"]

MAX_TEXT_LENGTH = 300


def _clean_text(value: str) -> str:
    value = " ".join(value.split())
    if not value:
        raise ValueError("must not be empty")
    if len(value) > MAX_TEXT_LENGTH:
        raise ValueError(f"must be at most {MAX_TEXT_LENGTH} characters, got {len(value)}: shorten it")
    return value


class DefectClassification(BaseModel):
    # Declared first on purpose: the model writes a short description before it picks the labels.
    # It is also reused as the anonymized description of the closed case, so it must not contain names.
    description: str
    defect_type: DefectTypeLiteral
    severity: SeverityLiteral
    confidence: ConfidenceLiteral

    @field_validator("description")
    @classmethod
    def description_is_short(cls, v: str) -> str:
        return _clean_text(v)


class RedoProposal(BaseModel):
    # The model picks a number from the list in the prompt; we map it back to an operation id ourselves.
    # The range is checked by the caller, which knows the list length (same approach as order drafting).
    operation_number: int
    likely_cause: str
    recommendation: str

    @field_validator("operation_number")
    @classmethod
    def operation_number_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("operation_number must be at least 1")
        return v

    @field_validator("likely_cause", "recommendation")
    @classmethod
    def text_is_short(cls, v: str) -> str:
        return _clean_text(v)
