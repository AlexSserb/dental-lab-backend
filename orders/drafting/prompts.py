from datetime import date

from orders.models import ToothColors

SYSTEM_TEMPLATE = """You turn a dentist's free-text request into a structured dental lab order. The text is in Russian.

Today is {today}.

Available work types (use only these numbers):
{work_types}

Rules:
- works: one item per kind of work. work_type_number is a number from the list above; choose the closest match. If nothing matches, return an empty works list.
- teeth: two-digit FDI tooth numbers mentioned in the text (11-18, 21-28, 31-38, 41-48). Never invent teeth.
- amount: number of units of that work; normally equal to the number of teeth.
- tooth_color: one of {colors}, or null if the text names no colour.
- days_from_now: deadline as a number of days from today ("через 10 дней" -> 10, "через две недели" -> 14), or null.
- comment: any extra wishes from the text that fit nowhere else, or null.

Examples:
Text: "Циркониевая коронка на 21 и 22, цвет A2, нужно через 10 дней"
Answer: {{"works":[{{"work_type_number":1,"teeth":[21,22],"amount":2}}],"tooth_color":"A2","days_from_now":10,"comment":null}}
Text: "мост 34-36 из металлокерамики, нужен через неделю, аккуратно с контактами"
Answer: {{"works":[{{"work_type_number":2,"teeth":[34,35,36],"amount":3}}],"tooth_color":null,"days_from_now":7,"comment":"аккуратно с контактами"}}
(The numbers 1 and 2 in the examples are illustrative; always use the list above.)"""


def build_system_prompt(work_type_names: list[str], today: date) -> str:
    numbered = "\n".join(f"{i}. {name}" for i, name in enumerate(work_type_names, start=1))
    return SYSTEM_TEMPLATE.format(today=today.isoformat(), work_types=numbered, colors=", ".join(ToothColors.values))
