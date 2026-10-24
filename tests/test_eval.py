import unittest

from adaptive.domains import get_pack
from adaptive.evaluation.harness import EvaluationHarness, evaluate_all_subjects


class TestEvaluationHarness(unittest.TestCase):
    """Regression gate: the AURA engine must keep passing its gold scenarios."""

    def setUp(self):
        self.results = evaluate_all_subjects(active=True, pack_for=lambda s: get_pack(s))

    def test_dsa_gold_scenarios_pass(self):
        rep = self.results["DSA"]
        self.assertGreaterEqual(rep["scenario_count"], 4)
        self.assertEqual(rep["top1_gap_accuracy"], 1.0)
        self.assertEqual(rep["top3_gap_recall"], 1.0)
        self.assertEqual(rep["abstention_accuracy"], 1.0)
        self.assertGreaterEqual(rep["calibration"]["logged_records"], 4)

    def test_biology_gold_scenarios_pass(self):
        rep = self.results["Biology"]
        self.assertGreaterEqual(rep["scenario_count"], 4)
        self.assertEqual(rep["top1_gap_accuracy"], 1.0)
        self.assertEqual(rep["top3_gap_recall"], 1.0)
        self.assertEqual(rep["abstention_accuracy"], 1.0)
        self.assertGreaterEqual(rep["calibration"]["logged_records"], 4)

    def test_active_beats_passive(self):
        for subject in ("DSA", "Biology"):
            pack = get_pack(subject)
            harness = EvaluationHarness(pack)
            passive = harness.evaluate(subject, active=False)
            active = harness.evaluate(subject, active=True)
            self.assertGreaterEqual(
                active["top1_gap_accuracy"], passive["top1_gap_accuracy"],
                msg=f"{subject}: active should not regress passive accuracy",
            )


if __name__ == "__main__":
    unittest.main()