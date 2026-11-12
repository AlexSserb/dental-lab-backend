import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.postgres.search import SearchVector
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings

from core.tests.base_testcase import BaseTestCase
from knowledge.models import Chunk, Document
from knowledge.services.chunking_service import ChunkingService
from knowledge.services.ingest_service import IngestService
from knowledge.services.rerank_service import RerankService
from knowledge.services.retrieval_service import (
    RetrievalService, RetrievedChunk, build_keyword_query, reciprocal_rank_fusion,
)
from llm.exceptions import LlmUnavailable

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


def retrieved(text, distance, path="defects/a.md", title="Скол керамики", rerank_score=None):
    document = SimpleNamespace(path=path, title=title, doc_type="defect", operation_type="Керамика")
    return RetrievedChunk(chunk=SimpleNamespace(text=text, document=document), distance=distance,
                          rerank_score=rerank_score)


@override_settings(KNOWLEDGE_TOP_K=4, KNOWLEDGE_MAX_DISTANCE=0.55)
class AskKnowledgeBaseTests(BaseTestCase):
    url = "/api/knowledge/ask/"

    def setUp(self):
        cache.clear()  # throttle counters live in the cache

    def ask(self, search_result=None, answer="Охлаждайте медленно [1].", llm_error=None, **payload):
        payload.setdefault("question", "Что делать, если скол керамики?")
        with patch("knowledge.services.answer_service.RetrievalService.search", return_value=search_result or []) as search, \
                patch("knowledge.services.answer_service.call_text", return_value=answer, side_effect=llm_error) as llm:
            response = self.client.post(self.url, payload, format="json")
        return response, search, llm

    def test_physician_is_forbidden(self):
        self.set_up_for_physician()
        response, _, _ = self.ask([retrieved("t", 0.2)])
        self.assertEqual(response.status_code, 403)

    def test_tech_gets_answer_with_sources_and_citation_flags(self):
        self.set_up_for_tech()
        items = [retrieved("Причины: быстрое охлаждение", 0.2), retrieved("Решение: корректировочная масса", 0.3)]
        response, _, llm = self.ask(items, answer="Причина — быстрое охлаждение [1].")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["answered"])
        self.assertEqual([(s["number"], s["cited"]) for s in data["sources"]], [(1, True), (2, False)])
        self.assertEqual(data["sources"][0]["documentTitle"], "Скол керамики")
        prompt = llm.call_args.kwargs["user_text"]
        self.assertIn("[1] Причины: быстрое охлаждение", prompt)
        self.assertIn("Вопрос: Что делать, если скол керамики?", prompt)

    def test_far_fragments_are_dropped_and_llm_is_not_called(self):
        self.set_up_for_admin()
        response, _, llm = self.ask([retrieved("unrelated", 0.7)])
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["answered"])
        self.assertEqual(response.json()["sources"], [])
        llm.assert_not_called()

    def test_operation_type_filter_is_passed_to_retrieval(self):
        self.set_up_for_admin()
        _, search, _ = self.ask([retrieved("t", 0.2)], operation_type="Керамика")
        self.assertEqual(search.call_args.args[2], "Керамика")

    def test_validation(self):
        self.set_up_for_admin()
        self.assertEqual(self.ask(question="")[0].status_code, 400)
        self.assertEqual(self.ask(question="x" * 501)[0].status_code, 400)
        self.assertEqual(self.ask(operation_type="Бухгалтерия")[0].status_code, 400)

    def test_llm_failure_is_503(self):
        self.set_up_for_admin()
        response, _, _ = self.ask([retrieved("t", 0.2)], llm_error=LlmUnavailable("down"))
        self.assertEqual(response.status_code, 503)


class ReciprocalRankFusionTests(SimpleTestCase):
    def test_item_found_by_both_searches_wins(self):
        fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "d"]])
        self.assertEqual([item for item, _ in fused], ["b", "a", "d", "c"])

    def test_scores_use_rank_positions_only(self):
        fused = dict(reciprocal_rank_fusion([["a", "b"], ["b"]], k=60))
        self.assertAlmostEqual(fused["a"], 1 / 61)
        self.assertAlmostEqual(fused["b"], 1 / 62 + 1 / 61)

    def test_empty_and_single_list(self):
        self.assertEqual(reciprocal_rank_fusion([]), [])
        self.assertEqual([item for item, _ in reciprocal_rank_fusion([["x", "y"], []])], ["x", "y"])

    def test_keyword_query(self):
        self.assertIsNone(build_keyword_query("? ! a"))
        self.assertIsNotNone(build_keyword_query("Как прессовать e.max?"))


def unit_vector(index):
    vector = [0.0] * 1024
    vector[index] = 1.0
    return vector


class HybridSearchTests(TestCase):
    """Vectors are hand-made: the question points at chunk A, but only chunk B contains the rare word."""

    def setUp(self):
        document = Document.objects.create(
            path="d.md", title="Док", doc_type="procedure", operation_type="Модели", content_hash="h",
        )
        self.a = Chunk.objects.create(document=document, position=0, text="Общее описание процесса", embedding=unit_vector(0))
        self.b = Chunk.objects.create(document=document, position=1, text="Штифты Пиндекса ставят параллельно", embedding=unit_vector(1))
        self.c = Chunk.objects.create(document=document, position=2, text="Другое", embedding=unit_vector(2))
        Chunk.objects.update(search_vector=SearchVector("text", config="russian"))
        patcher = patch("knowledge.services.retrieval_service.EmbeddingService.embed", return_value=[unit_vector(0)])
        patcher.start()
        self.addCleanup(patcher.stop)

    def ids(self, mode, k=3):
        return [item.chunk.id for item in RetrievalService.search("Пиндекса", k, mode=mode)]

    def test_dense_ranks_by_vector_only(self):
        self.assertEqual(self.ids("dense")[0], self.a.id)

    def test_keyword_finds_the_rare_word_that_vectors_miss(self):
        self.assertEqual(self.ids("keyword"), [self.b.id])

    def test_hybrid_contains_both_and_reports_who_found_what(self):
        items = RetrievalService.search("Пиндекса", 3, mode="hybrid")
        by_id = {item.chunk.id: item for item in items}
        self.assertIn(self.b.id, by_id)  # keyword rescued it
        self.assertEqual(by_id[self.a.id].found_by, ["vector"])
        self.assertEqual(sorted(by_id[self.b.id].found_by), ["keyword", "vector"])
        self.assertAlmostEqual(by_id[self.a.id].distance, 0.0)
        self.assertTrue(all(item.score for item in items))

    def test_operation_type_filter_applies_to_both_searches(self):
        other = Document.objects.create(path="o.md", title="О", doc_type="x", operation_type="Керамика", content_hash="h2")
        Chunk.objects.create(document=other, position=0, text="Пиндекса", embedding=unit_vector(0),
                             search_vector=None)
        Chunk.objects.filter(document=other).update(search_vector=SearchVector("text", config="russian"))
        items = RetrievalService.search("Пиндекса", 10, operation_type="Модели", mode="hybrid")
        self.assertTrue(items)
        self.assertTrue(all(item.chunk.document.operation_type == "Модели" for item in items))


class RerankServiceTests(SimpleTestCase):
    def test_reorders_by_cross_encoder_score_and_keeps_top_n(self):
        items = [retrieved("a", 0.1), retrieved("b", 0.2), retrieved("c", 0.3)]
        fake_model = SimpleNamespace(rerank=lambda query, docs: [-3.0, 2.5, -9.0])
        with patch("knowledge.services.rerank_service.get_reranker", return_value=fake_model):
            result = RerankService.rerank("q", items, top_n=2)
        self.assertEqual([i.chunk.text for i in result], ["b", "a"])
        self.assertEqual([i.rerank_score for i in result], [2.5, -3.0])

    def test_empty_candidates_do_not_load_the_model(self):
        with patch("knowledge.services.rerank_service.get_reranker") as get_model:
            self.assertEqual(RerankService.rerank("q", [], top_n=4), [])
        get_model.assert_not_called()


@override_settings(RERANK_ENABLED=True, KNOWLEDGE_MIN_RERANK_SCORE=-5.0, KNOWLEDGE_MAX_DISTANCE=0.55)
class AskWithRerankTests(BaseTestCase):
    url = "/api/knowledge/ask/"

    def setUp(self):
        cache.clear()
        self.set_up_for_admin()

    def ask(self, items):
        with patch("knowledge.services.answer_service.RetrievalService.search", return_value=items) as search, \
                patch("knowledge.services.answer_service.call_text", return_value="Ответ [1]") as llm:
            response = self.client.post(self.url, {"question": "вопрос"}, format="json")
        return response, search, llm

    def test_uses_rerank_mode_and_filters_by_rerank_score_not_distance(self):
        items = [
            retrieved("good", distance=0.9, rerank_score=1.0),    # far by vectors, but the reranker likes it
            retrieved("weak", distance=0.1, rerank_score=-7.0),   # close by vectors, but the reranker rejects it
        ]
        response, search, _ = self.ask(items)
        self.assertEqual(search.call_args.kwargs["mode"], "rerank")
        self.assertEqual([s["fragment"] for s in response.json()["sources"]], ["good"])

    def test_nothing_above_threshold_means_no_llm_call(self):
        response, _, llm = self.ask([retrieved("x", 0.2, rerank_score=-11.0)])
        self.assertFalse(response.json()["answered"])
        llm.assert_not_called()

    @override_settings(RERANK_ENABLED=False)
    def test_disabled_falls_back_to_hybrid_and_distance(self):
        response, search, _ = self.ask([retrieved("near", 0.2), retrieved("far", 0.8)])
        self.assertEqual(search.call_args.kwargs["mode"], "hybrid")
        self.assertEqual([s["fragment"] for s in response.json()["sources"]], ["near"])
