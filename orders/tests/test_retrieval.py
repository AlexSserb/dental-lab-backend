from django.test import SimpleTestCase

from orders.drafting.prompts import SYSTEM_PROMPT, build_user_message
from orders.drafting.retrieval import Candidate, select_candidates

CATALOG = [
    Candidate(1, "Циркониевая коронка", usage=5),
    Candidate(2, "Металлокерамическая коронка", usage=50),
    Candidate(3, "Металлокерамический мост", usage=20),
    Candidate(4, "Винир керамический", usage=1),
    Candidate(5, "Съемный протез акриловый", usage=3),
    Candidate(6, "Вкладка культевая", usage=2),
]


def names(cands):
    return [c.name for c in cands]


class SelectCandidatesTest(SimpleTestCase):
    def test_small_catalog_is_returned_whole_and_sorted(self):
        res = select_candidates("что угодно", CATALOG, limit=10)
        self.assertEqual(names(res), sorted(c.name for c in CATALOG))

    def test_lexical_match_wins_over_popularity(self):
        res = select_candidates("циркониевая коронка на 21", CATALOG, limit=2)
        self.assertIn("Циркониевая коронка", names(res))

    def test_rare_word_outweighs_common_word(self):
        # "коронка" is in two names, "циркониевая" only in one
        res = select_candidates("циркониевая коронка", CATALOG, limit=1)
        self.assertEqual(names(res), ["Циркониевая коронка"])

    def test_word_forms_match(self):
        res = select_candidates("нужны виниры", CATALOG, limit=1)
        self.assertEqual(names(res), ["Винир керамический"])
        res = select_candidates("два моста", CATALOG, limit=1)  # "мост" / "моста"
        self.assertEqual(names(res), ["Металлокерамический мост"])

    def test_names_differing_only_by_number_are_distinguished(self):
        catalog = [Candidate(i, f"Работа {i}", usage=10 - i) for i in range(1, 6)]
        res = select_candidates("Работа 5 на 36", catalog, limit=1)
        self.assertEqual(names(res), ["Работа 5"])

    def test_no_match_falls_back_to_most_used(self):
        res = select_candidates("абракадабра", CATALOG, limit=2)
        self.assertEqual(set(names(res)), {"Металлокерамическая коронка", "Металлокерамический мост"})

    def test_padding_keeps_matches_and_adds_popular(self):
        res = select_candidates("винир", CATALOG, limit=3)
        self.assertEqual(len(res), 3)
        self.assertIn("Винир керамический", names(res))
        self.assertIn("Металлокерамическая коронка", names(res))

    def test_result_is_sorted_by_name_and_never_exceeds_limit(self):
        res = select_candidates("коронка", CATALOG, limit=4)
        self.assertEqual(len(res), 4)
        self.assertEqual(names(res), sorted(names(res)))


class PromptLayoutTest(SimpleTestCase):
    def test_user_message_shape(self):
        from datetime import date
        msg = build_user_message(["A", "B"], date(2026, 1, 15), "текст")
        self.assertEqual(msg, "Work types:\n1. A\n2. B\n\nToday: 2026-01-15\n\nRequest: текст")

    def test_system_prompt_is_static(self):
        self.assertNotIn("Today is", SYSTEM_PROMPT)
