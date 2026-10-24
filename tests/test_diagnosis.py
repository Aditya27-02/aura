import unittest

from adaptive.core.diagnosis import DiagnosisEngine, SignalModel, entropy, information_gain
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.domains import get_pack
from adaptive.types import BKTParams, Question


class TestInformationGain(unittest.TestCase):
    def test_sharp_question_has_higher_ig(self):
        prior = {"a": 0.5, "b": 0.5}
        sharp = Question(
            id="sharp", concept_id="c", kind="diagnostic",
            prompt="?", options=["x", "y"], cost=1.0,
            likelihood={"a": [0.95, 0.05], "b": [0.05, 0.95]},
        )
        flat = Question(
            id="flat", concept_id="c", kind="diagnostic",
            prompt="?", options=["x", "y"], cost=1.0,
            likelihood={"a": [0.5, 0.5], "b": [0.5, 0.5]},
        )
        self.assertGreater(information_gain(prior, sharp), information_gain(prior, flat))
        self.assertAlmostEqual(information_gain(prior, flat), 0.0, places=6)


class TestDiagnosisEngine(unittest.TestCase):
    def setUp(self):
        self.pack = get_pack("DSA")
        self.state = LearnerStateEngine(self.pack.bkt_defaults)
        self.engine = DiagnosisEngine(self.pack.graph, self.state, self.pack.signal_model)

    def _code_event(self, failure_classes, pattern, recurrence=False):
        return self.pack.evidence_adapter(
            {
                "session_id": "s1",
                "timestamp": "2026-08-17T22:00:00+05:30",
                "event_id": "evt-1",
                "concept": "binary_search",
                "concept_strengths": [1.0, 0.35, 0.2],
                "secondary_concepts": ["boundary_handling"],
                "test_results": {"passed": ["normal"], "failed": failure_classes},
                "failure_classes": failure_classes,
                "static_pattern": pattern,
                "recurrence": recurrence,
                "code": "while low < high: low = mid",
            }
        )

    def test_hypotheses_include_prereqs_and_misconceptions(self):
        event = self._code_event(["left_boundary"], "low_mid_no_increment", True)
        hyps = self.engine.generate_hypotheses("binary_search", event)
        kinds = {h.kind for h in hyps}
        self.assertIn("prerequisite_gap", kinds)
        self.assertIn("misconception", kinds)
        self.assertTrue(any(h.concept_id == "mc_boundary_update" for h in hyps))
        self.assertAlmostEqual(sum(h.posterior for h in hyps), 1.0, places=6)

    def test_strong_signal_concentrates_posterior(self):
        event = self._code_event(["left_boundary", "single_element"], "low_mid_no_increment", True)
        hyps = self.engine.generate_hypotheses("binary_search", event)
        self.engine.update_from_evidence(hyps, event)
        top = self.engine.top_hypothesis(hyps)
        self.assertEqual(top.concept_id, "mc_boundary_update")
        self.assertGreater(top.posterior, 0.5)

    def _pass_event(self):
        return self.pack.evidence_adapter(
            {
                "session_id": "s0",
                "timestamp": "2026-08-16T19:00:00+05:30",
                "event_id": "evt-pass",
                "concept": "binary_search",
                "concept_strengths": [1.0, 0.35, 0.2],
                "secondary_concepts": [],
                "test_results": {"passed": ["normal", "left_boundary", "single_element"], "failed": []},
                "failure_classes": [],
                "static_pattern": None,
                "recurrence": False,
            }
        )

    def test_active_diagnosis_converges_to_true_gap(self):
        # healthy history first, then a one-off off-by-one on the left bound
        # (mirrors gold scenario dsa-02)
        self.state.apply(self._pass_event())
        event = self._code_event(["left_boundary"], "off_by_one_bound", False)
        hyps = self.engine.generate_hypotheses("binary_search", event)
        self.engine.update_from_evidence(hyps, event)
        initial = self.engine.entropy_of(hyps)
        self.assertFalse(self.engine.clears_confidence(hyps))

        result = self.engine.run_active_diagnosis(hyps, self.pack.questions("diagnostic"), true_label="mc_off_by_one", seed=7)
        self.assertEqual(result["top_hypothesis"], "mc_off_by_one")
        self.assertGreater(result["turns"], 0)
        self.assertLess(result["final_entropy"], initial)

    def test_uninformative_learner_stays_in_sufficient(self):
        event = self._code_event(["single_element"], "off_by_one_bound", False)
        hyps = self.engine.generate_hypotheses("binary_search", event)
        self.engine.update_from_evidence(hyps, event)
        result = self.engine.run_active_diagnosis(hyps, self.pack.questions("diagnostic"), true_label=None, seed=1, informative=False)
        self.assertTrue(result["insufficient_evidence"])
        self.assertEqual(result["turns"], 0)

    def test_abstention_reported_for_weak_evidence(self):
        event = self._code_event(["single_element"], "off_by_one_bound", False)
        hyps = self.engine.generate_hypotheses("binary_search", event)
        self.engine.update_from_evidence(hyps, event)
        result = self.engine.run_active_diagnosis(hyps, self.pack.questions("diagnostic"), informative=False)
        self.assertTrue(result["insufficient_evidence"])


if __name__ == "__main__":
    unittest.main()