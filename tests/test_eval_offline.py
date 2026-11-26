import unittest
from evals.run_offline import run, inspect_output, normalize


class OfflineEvaluationTests(unittest.TestCase):
    def test_all_expected_outcomes_and_repeatability(self):
        first = run()
        self.assertEqual(first, run())
        self.assertEqual(first["cases"], 4)
        self.assertEqual(first["executions"], 20)
        self.assertEqual(first["passed"], 20)
        self.assertIsNone(first["live_model_quality"])
        self.assertIsNone(first["human_review"])

    def test_negative_variants_fail_exactly_one_check(self):
        for item in run()["observations"]:
            failures = sum(not value for value in item["actual"].values())
            self.assertEqual(failures, 0 if item["variant"] == "reference" else 1)

    def test_unicode_and_output_size(self):
        self.assertEqual(normalize("RE\u0301FÉRENCE"), "référence")
        with self.assertRaises(ValueError):
            inspect_output({}, "x" * 65537)
