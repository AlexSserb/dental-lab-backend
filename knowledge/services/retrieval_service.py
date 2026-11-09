from dataclasses import dataclass, field
from typing import Hashable, Literal

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F
from pgvector.django import CosineDistance

from knowledge.models import Chunk
from knowledge.services.embedding_service import EmbeddingService

Mode = Literal["dense", "keyword", "hybrid"]
SEARCH_CONFIG = "russian"  # same text-search configuration that ingest uses to fill Chunk.search_vector
RRF_K = 60  # standard RRF constant: damps the advantage of rank 1 over rank 2
MIN_TOKEN_LENGTH = 2

_EDGE_PUNCTUATION = ".,;:!?()[]{}\"'«»—–-"


@dataclass
class RetrievedChunk:
    chunk: Chunk
    distance: float  # cosine distance to the question: 0 = identical, 2 = opposite (always computed, any mode)
    score: float | None = None  # RRF score (hybrid mode only), higher is better
    found_by: list[str] = field(default_factory=list)  # which searches returned it: "vector" and/or "keyword"


def reciprocal_rank_fusion(rankings: list[list[Hashable]], k: int = RRF_K) -> list[tuple[Hashable, float]]:
    """
    Merge several ranked lists of ids into one. An item scores 1 / (k + rank) in every list that contains it
    (rank starts at 1), the scores are summed, items are sorted by the sum. Only positions matter, never the raw
    scores, so lists that are not comparable (cosine distance vs full-text rank) can be merged directly.
    """
    scores: dict[Hashable, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, 1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)


def build_keyword_query(text: str) -> SearchQuery | None:
    """
    OR of the question's words, stemmed by the Russian configuration (стоп-слова are dropped by Postgres).
    OR instead of AND: a natural-language question rarely has all its words in a single chunk, and ts_rank
    then ranks chunks higher when they match more of the words.
    """
    # Split on whitespace only: tokens like "e.max" or "CAD/CAM" must reach Postgres whole, because its parser
    # indexes them as single tokens and a query split into "e" + "max" would never match.
    words = [w for w in (raw.strip(_EDGE_PUNCTUATION) for raw in text.lower().split()) if len(w) >= MIN_TOKEN_LENGTH]
    query: SearchQuery | None = None
    for word in dict.fromkeys(words):  # unique, keeps order
        part = SearchQuery(word, config=SEARCH_CONFIG)
        query = part if query is None else query | part
    return query


class RetrievalService:
    @staticmethod
    def search(
        query: str, k: int = 5, operation_type: str | None = None, mode: Mode = "hybrid",
    ) -> list[RetrievedChunk]:
        """
        Top `k` chunks for `query`.
          dense   - nearest by meaning (pgvector, cosine distance)
          keyword - best word matches (Postgres full-text search)
          hybrid  - both searches merged with Reciprocal Rank Fusion (default)
        """
        pool = max(k * 4, 20)  # candidates taken from each search before merging
        vector = EmbeddingService.embed([query])[0]

        dense = RetrievalService._dense(vector, pool, operation_type)
        if mode == "dense":
            return dense[:k]

        keyword = RetrievalService._keyword(query, vector, pool, operation_type)
        if mode == "keyword":
            return keyword[:k]

        return RetrievalService._fuse(dense, keyword)[:k]

    @staticmethod
    def _base_queryset(vector: list[float], operation_type: str | None):
        queryset = Chunk.objects.select_related("document").annotate(distance=CosineDistance("embedding", vector))
        if operation_type:
            queryset = queryset.filter(document__operation_type=operation_type)
        return queryset

    @staticmethod
    def _dense(vector: list[float], limit: int, operation_type: str | None) -> list[RetrievedChunk]:
        rows = RetrievalService._base_queryset(vector, operation_type).order_by("distance")[:limit]
        return [RetrievedChunk(chunk=row, distance=row.distance, found_by=["vector"]) for row in rows]

    @staticmethod
    def _keyword(query: str, vector: list[float], limit: int, operation_type: str | None) -> list[RetrievedChunk]:
        search_query = build_keyword_query(query)
        if search_query is None:
            return []
        rows = (
            RetrievalService._base_queryset(vector, operation_type)
            .filter(search_vector=search_query)
            .annotate(rank=SearchRank(F("search_vector"), search_query))
            .order_by("-rank", "distance")[:limit]
        )
        return [RetrievedChunk(chunk=row, distance=row.distance, found_by=["keyword"]) for row in rows]

    @staticmethod
    def _fuse(dense: list[RetrievedChunk], keyword: list[RetrievedChunk]) -> list[RetrievedChunk]:
        by_id: dict = {}
        for item in dense + keyword:
            if item.chunk.id in by_id:
                by_id[item.chunk.id].found_by.extend(item.found_by)
            else:
                by_id[item.chunk.id] = item

        fused = reciprocal_rank_fusion([[i.chunk.id for i in dense], [i.chunk.id for i in keyword]])
        result = []
        for chunk_id, score in fused:
            item = by_id[chunk_id]
            item.score = score
            result.append(item)
        return result
