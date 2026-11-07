from django.conf import settings

from knowledge.models import Chunk
from llm.client import get_client

BATCH_SIZE = 16


class EmbeddingService:
    @staticmethod
    def embed(texts: list[str]) -> list[list[float]]:
        """Embed texts with the configured model, in batches (one HTTP call per batch)."""
        expected = Chunk._meta.get_field("embedding").dimensions
        client = get_client()
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            batch = texts[start:start + BATCH_SIZE]
            response = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=batch)
            vectors.extend(item.embedding for item in response.data)

        if len(vectors) != len(texts):
            raise ValueError(f"Expected {len(texts)} embeddings, got {len(vectors)}")
        for vector in vectors:
            if len(vector) != expected:
                raise ValueError(
                    f"Embedding model '{settings.EMBEDDING_MODEL}' returned {len(vector)} dimensions, "
                    f"but Chunk.embedding expects {expected}"
                )
        return vectors
