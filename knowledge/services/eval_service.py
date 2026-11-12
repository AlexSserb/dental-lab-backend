import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from knowledge.services.retrieval_service import Mode, RetrievalService, RetrievedChunk

DEFAULT_QUESTIONS = Path(__file__).resolve().parent.parent / "evals" / "retrieval_questions.json"
RETRIEVAL_DEPTH = 30  # chunks fetched per question, then collapsed to distinct documents
Searcher = Callable[[str, int], list[RetrievedChunk]]


@dataclass
class CaseResult:
    question: str
    expected: list[str]
    ranked_documents: list[str]  # distinct document paths, best first
    best_distance: float | None
    rank: int | None  # 1-based rank of the first expected document, None if not found
    best_rerank_score: float | None = None  # highest cross-encoder score among the results (rerank mode only)


@dataclass
class EvalReport:
    cases: list[CaseResult] = field(default_factory=list)
    ks: tuple[int, ...] = (1, 3, 5)

    @property
    def answerable(self) -> list[CaseResult]:
        return [c for c in self.cases if c.expected]

    @property
    def unanswerable(self) -> list[CaseResult]:
        return [c for c in self.cases if not c.expected]

    def hit_rate(self, k: int) -> float:
        cases = self.answerable
        return sum(1 for c in cases if c.rank is not None and c.rank <= k) / len(cases) if cases else 0.0

    @property
    def mrr(self) -> float:
        cases = self.answerable
        return sum(1 / c.rank for c in cases if c.rank) / len(cases) if cases else 0.0

    def failures(self, k: int) -> list[CaseResult]:
        return [c for c in self.answerable if c.rank is None or c.rank > k]


class EvalService:
    @staticmethod
    def load_questions(path: Path = DEFAULT_QUESTIONS) -> list[dict]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def run(questions: list[dict], searcher: Searcher | None = None, mode: Mode = "hybrid") -> EvalReport:
        """Retrieval-only evaluation. A hit means any expected document is among the top-k *distinct documents*."""
        searcher = searcher or (lambda question, k: RetrievalService.search(question, k, mode=mode))
        report = EvalReport()
        for case in questions:
            retrieved = searcher(case["question"], RETRIEVAL_DEPTH)
            ranked: list[str] = []
            for item in retrieved:
                path = item.chunk.document.path
                if path not in ranked:
                    ranked.append(path)
            rank = next((i for i, path in enumerate(ranked, 1) if path in case["expected"]), None)
            report.cases.append(CaseResult(
                question=case["question"],
                expected=case["expected"],
                ranked_documents=ranked,
                best_distance=min((item.distance for item in retrieved), default=None),
                rank=rank,
                best_rerank_score=max((i.rerank_score for i in retrieved if i.rerank_score is not None), default=None),
            ))
        return report
