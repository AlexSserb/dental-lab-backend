from datetime import date, timedelta

from django.conf import settings
from django.db.models import Count

from llm.service import call_structured
from works.models import WorkType

from .prompts import build_system_prompt, build_user_message
from .retrieval import Candidate, select_candidates
from .schemas import OrderDraft

FEATURE = "order_draft"


def draft_order_from_text(text: str, user=None, today: date | None = None) -> dict:
    """
    Turn free text into a draft order. Nothing is saved: the client shows the draft to the doctor,
    who confirms it through the regular create-order endpoint.
    """
    today = today or date.today()
    work_types = _pick_candidates(text)

    def check_business_rules(draft: OrderDraft) -> None:
        for work in draft.works:
            if not (1 <= work.work_type_number <= len(work_types)):
                raise ValueError(
                    f"work_type_number {work.work_type_number} is not in the list (valid: 1-{len(work_types)})"
                )

    draft = call_structured(
        feature=FEATURE,
        system=build_system_prompt(),
        user_text=build_user_message([wt.name for wt in work_types], today, text),
        schema=OrderDraft,
        validator=check_business_rules,
        user=user,
    )
    return _to_response(draft, work_types, today)


def _pick_candidates(text: str) -> list[Candidate]:
    """Active work types only (same set the UI offers), narrowed to the ones relevant to `text`."""
    catalog = [
        Candidate(id=wt.id, name=wt.name, usage=wt.usage)
        for wt in WorkType.objects.filter(is_active=True).annotate(usage=Count("works"))
    ]
    return select_candidates(text, catalog, settings.AI_MAX_CANDIDATES)


def _to_response(draft: OrderDraft, work_types: list[Candidate], today: date) -> dict:
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
