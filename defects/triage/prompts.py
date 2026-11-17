"""
Message builders of the defect triage workflow. The long, static system prompts are not here: they are files in
prompt_templates/ and are served by prompt_provider (optionally from the LangSmith prompt hub).
"""

MAX_COMMENT_LENGTH = 500


def _clean(text: str, limit: int = MAX_COMMENT_LENGTH) -> str:
    """Make free text safe to put between our own tags: no angle brackets, one line, bounded length."""
    return " ".join(text.replace("<", " ").replace(">", " ").split())[:limit]


def build_classify_message(work_names: list[str], comment: str) -> str:
    numbered = "\n".join(f"{i}. {name}" for i, name in enumerate(work_names, start=1)) or "(не указаны)"
    return f"Works:\n{numbered}\n\n<report>{_clean(comment) or 'комментарий не указан'}</report>"


def build_propose_message(
    description: str,
    defect_type: str,
    severity: str,
    operations: list[str],
    precedents: list[str],
    feedback: str = "",
) -> str:
    """
    `operations` are display lines like "Проектирование коронки (Циркониевая коронка)", in production order;
    `precedents` are ready-to-show texts of similar closed cases and knowledge base excerpts.
    """
    numbered_operations = "\n".join(f"{i}. {line}" for i, line in enumerate(operations, start=1))
    numbered_precedents = "\n".join(f"{i}. {_clean(text, 800)}" for i, text in enumerate(precedents, start=1))
    parts = [
        f"Defect: {_clean(description)} ({defect_type}, {severity})",
        f"Operations:\n{numbered_operations}",
        f"Precedents:\n{numbered_precedents or '(нет похожих случаев)'}",
    ]
    if feedback.strip():
        parts.append(f"<feedback>{_clean(feedback)}</feedback>")
    return "\n\n".join(parts)
