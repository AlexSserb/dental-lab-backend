"""Pydantic models describing what the LLM must return."""
from typing import Literal, Optional

from pydantic import BaseModel, field_validator

from orders.models import ToothColors

# Literal makes the allowed colours part of the JSON schema, so the model cannot invent "A5".
ToothColorLiteral = Literal[tuple(ToothColors.values)]  # type: ignore[valid-type]


class DraftWork(BaseModel):
    # The model picks a number from the list in the prompt; we map it back to a UUID ourselves.
    # Short numbers are cheaper than UUIDs and a small model cannot garble them.
    work_type_number: int
    teeth: list[int]
    amount: int

    @field_validator("teeth")
    @classmethod
    def teeth_in_fdi_range(cls, v: list[int]) -> list[int]:
        bad = [t for t in v if not (11 <= t <= 48 and 1 <= t % 10 <= 8 and 1 <= t // 10 <= 4)]
        if bad:
            raise ValueError(f"invalid tooth numbers {bad}: use two-digit FDI numbers 11-18, 21-28, 31-38, 41-48")
        return sorted(set(v))

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("amount must be at least 1")
        return v


class OrderDraft(BaseModel):
    works: list[DraftWork]
    tooth_color: Optional[ToothColorLiteral]
    # Relative deadline, e.g. "через 10 дней" -> 10. The date itself is computed in Python.
    days_from_now: Optional[int]
    # Anything from the text that did not fit into the other fields
    comment: Optional[str]

    @field_validator("days_from_now")
    @classmethod
    def deadline_reasonable(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 365):
            raise ValueError("days_from_now must be between 1 and 365")
        return v
