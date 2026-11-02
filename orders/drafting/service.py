from datetime import date, timedelta

from llm.service import call_structured
from works.models import WorkType

from .prompts import build_system_prompt
from .schemas import OrderDraft

FEATURE = "order_draft"


def draft_order_from_text(text: str, user=None, today: date | None = None) -> dict:
    """
    Turn free text into a draft order. Nothing is saved: the client shows the draft to the doctor,
    who confirms it through the regular create-order endpoint.
    """
    today = today or date.today()
    # Same ordering as WorkTypeList so numbers in the prompt are stable between calls
    work_types = list(WorkType.objects.order_by("name"))

    def check_business_rules(draft: OrderDraft) -> None:
        for work in draft.works:
            if not (1 <= work.work_type_number <= len(work_types)):
                raise ValueError(
                    f"work_type_number {work.work_type_number} is not in the list (valid: 1-{len(work_types)})"
                )

    draft = call_structured(
        feature=FEATURE,
        system=build_system_prompt([wt.name for wt in work_types], today),
        user_text=text,
        schema=OrderDraft,
        validator=check_business_rules,
        user=user,
    )
    return _to_response(draft, work_types, today)


def _to_response(draft: OrderDraft, work_types: list[WorkType], today: date) -> dict:
    warnings: list[str] = []
    works = []
    for w in draft.works:
        wt = work_types[w.work_type_number - 1]
        if not w.teeth:
            warnings.append(f"Для работы «{wt.name}» не указаны зубы")
        elif w.amount != len(w.teeth):
            warnings.append(f"Для работы «{wt.name}» количество ({w.amount}) не совпадает с числом зубов ({len(w.teeth)})")
        works.append({"work_type_id": wt.id, "work_type_name": wt.name, "teeth": w.teeth, "amount": w.amount})

    if not works:
        warnings.append("Не удалось определить работы. Заполните форму вручную")
    if draft.tooth_color is None:
        warnings.append("Цвет зуба не указан")

    return {
        "works": works,
        "tooth_color": draft.tooth_color,
        "deadline": today + timedelta(days=draft.days_from_now) if draft.days_from_now else None,
        "comment": draft.comment if works else None,  # a small model may chat when the text is off-topic
        "warnings": warnings,
    }
