import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path

from django.contrib.postgres.search import SearchVector
from django.db import transaction

from knowledge.models import Chunk, Document
from knowledge.services.chunking_service import ChunkingService
from knowledge.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

REQUIRED_META = ("title", "doc_type", "operation_type")


@dataclass
class IngestResult:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)


class IngestService:
    @staticmethod
    def ingest(root: Path, force: bool = False) -> IngestResult:
        """Sync every .md file under `root` into Document/Chunk. Unchanged files are skipped by content hash;
        documents whose files disappeared are deleted."""
        if not root.is_dir():
            raise FileNotFoundError(f"Knowledge base directory not found: {root}")

        result = IngestResult()
        seen: list[str] = []
        for file in sorted(root.rglob("*.md")):
            path = file.relative_to(root).as_posix()
            seen.append(path)
            outcome = IngestService._ingest_file(file, path, force)
            getattr(result, outcome).append(path)

        stale = Document.objects.exclude(path__in=seen)
        result.deleted = list(stale.values_list("path", flat=True))
        stale.delete()
        return result

    @staticmethod
    def _ingest_file(file: Path, path: str, force: bool) -> str:
        raw = file.read_text(encoding="utf-8")
        content_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        existing = Document.objects.filter(path=path).first()
        if existing and existing.content_hash == content_hash and not force:
            return "skipped"

        meta, body = ChunkingService.parse_frontmatter(raw)
        missing = [key for key in REQUIRED_META if not meta.get(key)]
        if missing:
            raise ValueError(f"{path}: missing frontmatter fields: {', '.join(missing)}")

        texts = ChunkingService.chunk_markdown(meta["title"], body)
        if not texts:
            raise ValueError(f"{path}: no chunks produced")
        vectors = EmbeddingService.embed(texts)  # network call kept outside the DB transaction

        with transaction.atomic():
            document, _ = Document.objects.update_or_create(
                path=path,
                defaults={
                    "title": meta["title"],
                    "doc_type": meta["doc_type"],
                    "operation_type": meta["operation_type"],
                    "content_hash": content_hash,
                },
            )
            document.chunks.all().delete()
            Chunk.objects.bulk_create(
                Chunk(document=document, position=i, text=text, embedding=vector)
                for i, (text, vector) in enumerate(zip(texts, vectors))
            )
            document.chunks.update(search_vector=SearchVector("text", config="russian"))

        logger.info("Ingested %s: %d chunks", path, len(texts))
        return "updated" if existing else "created"
