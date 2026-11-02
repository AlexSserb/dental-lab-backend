"""
Prompt layout, from most stable to least stable, so providers can reuse a cached prefix:

  system:  rules + colours + worked examples (identical for every request)
  user:    candidate work types, today's date, the doctor's text (changes per request)
"""
from datetime import date

from orders.models import ToothColors

SYSTEM_PROMPT = f"""You turn a dentist's free-text request into a structured dental lab order. The text is in Russian.
Each request contains a numbered list of available work types, today's date and the request text.

Rules:
- works: one item per kind of work. work_type_number is a number from the list in THAT request; choose the closest match. If nothing matches, return an empty works list.
- teeth: two-digit FDI tooth numbers mentioned in the text (11-18, 21-28, 31-38, 41-48). Never invent teeth.
- amount: number of units of that work; normally equal to the number of teeth.
- tooth_color: one of {", ".join(ToothColors.values)}, or null if the text names no colour.
- days_from_now: deadline as a number of days from today ("через 10 дней" -> 10, "через две недели" -> 14), or null.
- comment: any extra wishes from the text that fit nowhere else, or null.

Example 1
Work types:
1. Металлокерамический мост
2. Циркониевая коронка

Today: 2026-01-15

Request: Циркониевая коронка на 21 и 22, цвет A2, нужно через 10 дней
Answer: {{"works":[{{"work_type_number":2,"teeth":[21,22],"amount":2}}],"tooth_color":"A2","days_from_now":10,"comment":null}}

Example 2
Work types:
1. Металлокерамический мост
2. Циркониевая коронка

Today: 2026-01-15

Request: мост 34-36, нужен через неделю, аккуратно с контактами
Answer: {{"works":[{{"work_type_number":1,"teeth":[34,35,36],"amount":3}}],"tooth_color":null,"days_from_now":7,"comment":"аккуратно с контактами"}}"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def build_user_message(work_type_names: list[str], today: date, text: str) -> str:
    numbered = "\n".join(f"{i}. {name}" for i, name in enumerate(work_type_names, start=1))
    return f"Work types:\n{numbered}\n\nToday: {today.isoformat()}\n\nRequest: {text}"
