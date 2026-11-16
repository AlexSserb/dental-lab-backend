"""
The store of closed defect cases and the precedent retrieval for the propose step.

Precedents are ready-to-show texts: similar closed cases first (embedded with the same EmbeddingService as the
knowledge base), then KB defect documents as a fallback — at launch there are no cases, and the fallback is what
keeps the propose step useful from day one.
"""
from pgvector.django import CosineDistance

from defects.models import DefectCase
from knowledge.services.embedding_service import EmbeddingService
from knowledge.services.retrieval_service import RetrievalService

# How many precedents the propose prompt shows, and which KB documents may back it up.
CASE_TOP_K = 3
KB_DOC_TYPE = "defect"
# Above this cosine distance a closed case is not similar enough to be offered as a precedent.
MAX_CASE_DISTANCE = 0.8


def add_case(
    *,
    defect_type: str,
    severity: str,
    description: str,
    cause: str,
    resolution: str = "",
    operation_type=None,
    triage=None,
    source: str = DefectCase.Source.TRIAGE,
) -> DefectCase:
    """Store a closed defect as a precedent: the technical facts are joined into `search_text` and embedded."""
    search_text = _case_text(description, cause, resolution)
    embedding = EmbeddingService.embed([search_text])[0]
    return DefectCase.objects.create(
        defect_type=defect_type,
        severity=severity,
        description=description,
        cause=cause,
        resolution=resolution,
        operation_type=operation_type,
        triage=triage,
        source=source,
        search_text=search_text,
        embedding=embedding,
    )


def find_similar(description: str, k: int = CASE_TOP_K) -> list[DefectCase]:
    """The `k` stored cases nearest to `description` by cosine distance; cases without an embedding are skipped."""
    vector = EmbeddingService.embed([description])[0]
    rows = (
        DefectCase.objects
        .annotate(distance=CosineDistance("embedding", vector))
        .filter(distance__lte=MAX_CASE_DISTANCE)
        .order_by("distance")[:k]
    )
    return list(rows)


def get_precedents(description: str, k: int = CASE_TOP_K) -> list[str]:
    """
    `k` precedent texts for the propose prompt: closed cases first, KB defect documents fill the remainder.
    Each text is one line of the shape the propose prompt's example uses.
    """
    cases = find_similar(description, k)
    precedents = [case.search_text for case in cases]
    if len(precedents) < k:
        # Fallback: the KB holds curated defect instructions (doc_type: defect) for the days before real cases exist.
        for item in RetrievalService.search(description, k - len(precedents), doc_type=KB_DOC_TYPE, mode="dense"):
            precedents.append(item.chunk.text)
    return precedents


def _case_text(description: str, cause: str, resolution: str) -> str:
    text = f"{description} Причина: {cause}"
    if resolution.strip():
        text += f" Решение: {resolution}"
    return " ".join(text.split())
