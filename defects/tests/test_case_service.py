from unittest.mock import patch

from django.contrib.postgres.search import SearchVector
from django.test import TestCase

from defects.models import DefectCase, DefectSeverity, DefectType
from defects.triage import case_service
from defects.triage.case_service import add_case, find_similar, get_precedents
from knowledge.models import Chunk, Document


def unit_vector(index: int) -> list[float]:
    vector = [0.0] * 1024
    vector[index] = 1.0
    return vector


class AddCaseTest(TestCase):
    def test_embeds_the_search_text_and_stores_the_case(self):
        with patch("defects.triage.case_service.EmbeddingService.embed") as embed:
            embed.return_value = [unit_vector(0)]
            case = add_case(
                defect_type=DefectType.FIT, severity=DefectSeverity.MEDIUM,
                description="Коронка не садится.", cause="Малый цементный зазор.",
                resolution="Перефрезеровать.",
            )

        embed.assert_called_once()
        self.assertEqual(
            embed.call_args.args[0], ["Коронка не садится. Причина: Малый цементный зазор. Решение: Перефрезеровать."],
        )
        self.assertEqual(case.search_text, "Коронка не садится. Причина: Малый цементный зазор. Решение: Перефрезеровать.")
        self.assertEqual(case.embedding, unit_vector(0))
        self.assertEqual(case.source, DefectCase.Source.TRIAGE)

    def test_resolution_is_optional(self):
        with patch("defects.triage.case_service.EmbeddingService.embed") as embed:
            embed.return_value = [unit_vector(1)]
            case = add_case(
                defect_type=DefectType.COLOR, severity=DefectSeverity.LOW,
                description="Оттенок светлее заказа.", cause="Неверная краска.",
            )
        self.assertEqual(case.search_text, "Оттенок светлее заказа. Причина: Неверная краска.")
        self.assertEqual(case.resolution, "")


class FindSimilarTest(TestCase):
    def setUp(self):
        patcher = patch("defects.triage.case_service.EmbeddingService.embed", return_value=[unit_vector(0)])
        self.embed = patcher.start()
        self.addCleanup(patcher.stop)

    def test_empty_table_returns_nothing(self):
        self.embed.return_value = [unit_vector(0)]
        self.assertEqual(find_similar("Коронка не садится."), [])

    def test_ranked_by_cosine_distance(self):
        fit_case = add_case(
            defect_type=DefectType.FIT, severity=DefectSeverity.MEDIUM,
            description="Не садится", cause="Зазор", resolution="",
        )
        porosity_case = add_case(
            defect_type=DefectType.POROSITY, severity=DefectSeverity.LOW,
            description="Пузыри", cause="Влага", resolution="",
        )
        DefectCase.objects.filter(id=fit_case.id).update(embedding=unit_vector(0))
        # Near, but not identical: 45 degrees off the query vector (cosine distance ~0.29, inside the threshold).
        diagonal = [0.5] + [0.0] * 4 + [0.5] + [0.0] * 1018
        DefectCase.objects.filter(id=porosity_case.id).update(embedding=diagonal)

        self.embed.return_value = [unit_vector(0)]  # the query points at the fit case
        found = find_similar("Не садится", k=2)
        self.assertEqual([case.id for case in found], [fit_case.id, porosity_case.id])

    def test_far_cases_are_not_offered_as_precedents(self):
        case = add_case(
            defect_type=DefectType.FIT, severity=DefectSeverity.MEDIUM,
            description="Не садится", cause="Зазор", resolution="",
        )
        DefectCase.objects.filter(id=case.id).update(embedding=unit_vector(0))
        self.embed.return_value = [unit_vector(5)]  # orthogonal: unrelated defect
        self.assertEqual(find_similar("Пузыри"), [])

    def test_case_without_embedding_is_skipped(self):
        case = add_case(
            defect_type=DefectType.FIT, severity=DefectSeverity.MEDIUM,
            description="Не садится", cause="Зазор", resolution="",
        )
        DefectCase.objects.filter(id=case.id).update(embedding=None)
        self.embed.return_value = [unit_vector(0)]
        self.assertEqual(find_similar("Не садится"), [])


class GetPrecedentsTest(TestCase):
    """Cases come first; KB defect documents fill in while the case table is empty or not full yet."""

    def setUp(self):
        self.embed = patch("defects.triage.case_service.EmbeddingService.embed", return_value=[unit_vector(0)])
        self.embed.start()
        self.addCleanup(self.embed.stop)

    def make_kb(self, doc_type: str, texts: tuple[str, ...]) -> None:
        document = Document.objects.create(
            path=f"{doc_type}.md", title="Док", doc_type=doc_type, operation_type="Керамика", content_hash=doc_type,
        )
        for position, text in enumerate(texts):
            Chunk.objects.create(document=document, position=position, text=text, embedding=unit_vector(position))

    def test_empty_table_falls_back_to_kb_defect_documents(self):
        self.make_kb("defect", ("Инструкция: скол керамики.", "Другая инструкция"))
        self.make_kb("procedure", ("Это про общий процесс, не про дефекты",))

        precedents = get_precedents("Скол керамики", k=2)
        self.assertEqual(precedents, ["Инструкция: скол керамики.", "Другая инструкция"])

    def test_cases_come_first_and_kb_fills_the_remainder(self):
        self.make_kb("defect", ("Инструкция из базы знаний",))
        case = add_case(
            defect_type=DefectType.FIT, severity=DefectSeverity.MEDIUM,
            description="Не садится", cause="Зазор", resolution="",
        )
        DefectCase.objects.filter(id=case.id).update(embedding=unit_vector(0))

        precedents = get_precedents("Не садится", k=2)
        self.assertEqual(precedents[0], case.search_text)
        self.assertEqual(precedents[1], "Инструкция из базы знаний")

    def test_full_case_list_leaves_kb_out(self):
        self.make_kb("defect", ("Инструкция из базы знаний",))
        texts = [("Не садится " + str(i), "Причина", "") for i in range(3)]
        for description, cause, resolution in texts:
            case = add_case(defect_type=DefectType.FIT, severity=DefectSeverity.MEDIUM,
                            description=description, cause=cause, resolution=resolution)
            DefectCase.objects.filter(id=case.id).update(embedding=unit_vector(0))

        self.assertEqual(len(get_precedents("Не садится", k=3)), 3)
        self.assertNotIn("Инструкция из базы знаний", get_precedents("Не садится", k=3))


class DocTypeFilterTest(TestCase):
    """RetrievalService.search can narrow a search to one document kind."""

    def setUp(self):
        patcher = patch("knowledge.services.retrieval_service.EmbeddingService.embed", return_value=[unit_vector(0)])
        patcher.start()
        self.addCleanup(patcher.stop)
        defect = Document.objects.create(
            path="d.md", title="Дефект", doc_type="defect", operation_type="Керамика", content_hash="d",
        )
        procedure = Document.objects.create(
            path="p.md", title="Процесс", doc_type="procedure", operation_type="Керамика", content_hash="p",
        )
        self.defect_chunk = Chunk.objects.create(document=defect, position=0, text="Скол керамики", embedding=unit_vector(0))
        Chunk.objects.create(document=procedure, position=0, text="Скол керамики", embedding=unit_vector(0))

    def test_doc_type_filter_returns_only_that_kind(self):
        items = case_service.RetrievalService.search("Скол керамики", k=5, doc_type="defect", mode="dense")
        self.assertEqual([item.chunk.id for item in items], [self.defect_chunk.id])
