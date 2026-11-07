import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from knowledge.models import Chunk, Document
from knowledge.services.chunking_service import ChunkingService
from knowledge.services.ingest_service import IngestService

SAMPLE = """---
title: Скол керамики
doc_type: defect
operation_type: Керамика
---
# Скол керамики

## Причины
1. Быстрое охлаждение.
2. Разный КТР.

## Решение
Исправить массой.
"""


def fake_embed(texts):
    return [[0.1] * 1024 for _ in texts]


class ChunkingServiceTests(SimpleTestCase):
    def test_parse_frontmatter(self):
        meta, body = ChunkingService.parse_frontmatter(SAMPLE)
        self.assertEqual(meta, {"title": "Скол керамики", "doc_type": "defect", "operation_type": "Керамика"})
        self.assertTrue(body.startswith("# Скол керамики"))

    def test_no_frontmatter(self):
        self.assertEqual(ChunkingService.parse_frontmatter("text"), ({}, "text"))

    def test_chunk_per_section_with_title_prefix(self):
        _, body = ChunkingService.parse_frontmatter(SAMPLE)
        chunks = ChunkingService.chunk_markdown("Скол керамики", body)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(chunks[0].startswith("Скол керамики / Причины\n1. Быстрое"))
        self.assertTrue(chunks[1].startswith("Скол керамики / Решение\n"))

    def test_long_section_is_split_and_every_piece_keeps_prefix(self):
        body = "## Шаги\n" + "\n".join(f"{i}. " + "слово " * 20 for i in range(20))
        chunks = ChunkingService.chunk_markdown("Док", body, max_chars=300)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertTrue(chunk.startswith("Док / Шаги\n"))
            self.assertLessEqual(len(chunk), 300)


class IngestServiceTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "a.md").write_text(SAMPLE, encoding="utf-8")
        patcher = patch("knowledge.services.ingest_service.EmbeddingService.embed", side_effect=fake_embed)
        self.embed = patcher.start()
        self.addCleanup(patcher.stop)

    def test_create_then_skip_then_update_then_delete(self):
        result = IngestService.ingest(self.root)
        self.assertEqual(result.created, ["a.md"])
        self.assertEqual(Chunk.objects.count(), 2)
        self.assertEqual(Document.objects.get().doc_type, "defect")
        self.assertFalse(Chunk.objects.filter(search_vector__isnull=True).exists())

        self.assertEqual(IngestService.ingest(self.root).skipped, ["a.md"])

        (self.root / "a.md").write_text(SAMPLE + "\n## Профилактика\nМедленно охлаждать.\n", encoding="utf-8")
        self.assertEqual(IngestService.ingest(self.root).updated, ["a.md"])
        self.assertEqual(Chunk.objects.count(), 3)

        (self.root / "a.md").unlink()
        self.assertEqual(IngestService.ingest(self.root).deleted, ["a.md"])
        self.assertEqual(Document.objects.count(), 0)

    def test_missing_frontmatter_raises(self):
        (self.root / "bad.md").write_text("## x\ntext", encoding="utf-8")
        with self.assertRaisesMessage(ValueError, "missing frontmatter fields"):
            IngestService.ingest(self.root)


class EvalServiceTests(SimpleTestCase):
    @staticmethod
    def _searcher(mapping):
        from types import SimpleNamespace

        from knowledge.services.retrieval_service import RetrievedChunk

        def search(question, k):
            return [
                RetrievedChunk(chunk=SimpleNamespace(document=SimpleNamespace(path=path)), distance=0.1 * (i + 1))
                for i, path in enumerate(mapping[question])
            ]

        return search

    def test_metrics(self):
        from knowledge.services.eval_service import EvalService

        questions = [
            {"question": "q1", "expected": ["a.md"]},
            {"question": "q2", "expected": ["b.md"]},
            {"question": "q3", "expected": ["c.md"]},
            {"question": "q4", "expected": []},
        ]
        mapping = {
            "q1": ["a.md", "x.md"],              # rank 1
            "q2": ["x.md", "x.md", "b.md"],      # rank 2 (duplicates collapse to one document)
            "q3": ["x.md", "y.md"],              # miss
            "q4": ["x.md"],
        }
        report = EvalService.run(questions, searcher=self._searcher(mapping))

        self.assertEqual(len(report.answerable), 3)
        self.assertAlmostEqual(report.hit_rate(1), 1 / 3)
        self.assertAlmostEqual(report.hit_rate(3), 2 / 3)
        self.assertAlmostEqual(report.mrr, (1 + 0.5 + 0) / 3)
        self.assertEqual([c.question for c in report.failures(3)], ["q3"])
