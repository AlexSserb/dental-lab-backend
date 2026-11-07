import uuid
from typing import TYPE_CHECKING

from django.contrib.postgres.search import SearchVectorField
from django.db import models
from pgvector.django import HnswIndex, VectorField

from core.models import BaseModel


class Document(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    path = models.TextField(unique=True)
    title = models.TextField()
    doc_type = models.TextField()
    operation_type = models.TextField()
    content_hash = models.TextField()

    if TYPE_CHECKING:
        chunks: models.Manager["Chunk"]


class Chunk(BaseModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    position = models.PositiveIntegerField()
    text = models.TextField()
    # Must match the output size of the embedding model (bge-m3 -> 1024).
    embedding = VectorField(dimensions=1024)
    # Filled by the ingest step; used later for hybrid (full-text) search.
    search_vector = SearchVectorField(null=True)

    class Meta:
        ordering = ["document", "position"]
        constraints = [
            models.UniqueConstraint(fields=["document", "position"], name="unique_chunk_position_per_document"),
        ]
        indexes = [
            HnswIndex(
                name="chunk_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]
