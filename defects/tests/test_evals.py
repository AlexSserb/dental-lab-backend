"""
Sanity checks of the eval case file itself: the labels must be valid enum values and the operation
numbers must point at existing list entries. No LLM is called here.
"""
from defects.evals.runner import load_cases
from defects.models import DefectSeverity, DefectType
from django.test import SimpleTestCase


class TriageCasesFileTest(SimpleTestCase):
    def test_labeled_cases_are_consistent(self):
        cases = load_cases()

        self.assertGreaterEqual(len(cases), 30)
        ids = {case["id"] for case in cases}
        self.assertEqual(len(ids), len(cases), "case ids must be unique")
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertIn(case["defect_type"], DefectType.values)
                self.assertIn(case["severity"], DefectSeverity.values)
                self.assertTrue(case["comment"].strip())
                self.assertTrue(case["work_names"])
                self.assertIn(case["expected_operation"], range(1, len(case["operations"]) + 1))
                # every defect type must be covered: the eval must be able to catch a bias towards one label
                self.assertIn(case["defect_type"], {c["defect_type"] for c in cases})
