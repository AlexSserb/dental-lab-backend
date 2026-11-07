from dataclasses import dataclass

from pgvector.django import CosineDistance

from knowledge.models import Chunk
from knowledge.services.embedding_service import EmbeddingService


@dataclass
class RetrievedChunk:
    chunk: Chunk
    distance: float  # cosine distance: 0 = identical, 2 = opposite


class RetrievalService:
    @staticmethod
    def search(query: str, k: int = 5, operation_type: str | None = None) -> list[RetrievedChunk]:
        """Dense (vector) search: the `k` chunks closest to the query by cosine distance."""
        vector = EmbeddingService.embed([query])[0]
        queryset = Chunk.objects.select_related("document")
        if operation_type:
            queryset = queryset.filter(document__operation_type=operation_type)
        rows = queryset.annotate(distance=CosineDistance("embedding", vector)).order_by("distance")[:k]
        return [RetrievedChunk(chunk=row, distance=row.distance) for row in rows]
