import json
import unittest

from adaptive.core.session import AdaptiveSession
from adaptive.domains import get_pack
from adaptive.privacy.capsule import PRIVACY_CLAIM, build_capsule

PRIVACY_SENTENCE = (
    "Persistent personalization memory stays local; remote services receive only "
    "the minimum temporary context required for the current operation."
)


class TestPrivacyClaim(unittest.TestCase):
    def test_claim_is_verbatim(self):
        self.assertEqual(PRIVACY_CLAIM, PRIVACY_SENTENCE)


class TestPrivacyCapsule(unittest.TestCase):
    def setUp(self):
        self.pack = get_pack("DSA")
        self.session = AdaptiveSession(self.pack)
        self.session.start_session("PRIV-01")
        self.session.observe(
            {
                "timestamp": "2026-08-17T22:10:00+05:30",
                "concept": "binary_search",
                "secondary_concepts": ["boundary_handling"],
                "test_results": {"passed": ["normal_asc"], "failed": ["left_boundary", "single_element"]},
                "failure_classes": ["left_boundary", "single_element"],
                "static_pattern": "low_mid_no_increment",
                "recurrence": True,
                "code": "while low < high: low = mid",
            }
        )

    def test_capsule_has_plan_shape(self):
        cap = self.session.privacy_capsule()
        expected = {
            "subject", "target", "current_state", "relevant_history",
            "current_evidence", "retrieved_sources", "dry_run",
        }
        self.assertEqual(set(cap), expected)
        self.assertEqual(cap["subject"], "DSA")
        self.assertEqual(cap["target"], "binary_search")
        self.assertTrue(cap["dry_run"])
        self.assertLessEqual(len(cap["relevant_history"]), 5)
        self.assertLessEqual(len(cap["current_state"]), 6)

    def test_current_state_is_status_bands_not_probabilities(self):
        cap = self.session.privacy_capsule()
        for band in cap["current_state"].values():
            self.assertIn(band, {"verified", "developing", "needs_review", "active_blocker"})

    def test_retrieved_sources_reflect_bundle(self):
        bundle = self.session.retrieve("binary_search", "strict interval shrink mid plus one", k=3)
        cap = self.session.privacy_capsule(bundle=bundle)
        self.assertTrue(cap["retrieved_sources"])
        self.assertLessEqual(len(cap["retrieved_sources"]), 5)

    def test_capsule_is_json_serialisable(self):
        json.dumps(self.session.privacy_capsule())

    def test_bare_builder_respects_plan_shape(self):
        cap = build_capsule(
            subject="Biology",
            target="golgi",
            current_state={"RER": "developing", "Golgi": "needs_review"},
            relevant_history=["confused packaging function twice"],
            current_evidence="spoken answer transcript",
            retrieved_sources=["chunk-118", "chunk-121"],
        )
        self.assertEqual(cap["retrieved_sources"], ["chunk-118", "chunk-121"])
        self.assertEqual(cap["current_state"]["Golgi"], "needs_review")


class TestColdStartSameEngine(unittest.TestCase):
    """§7.6: cold start is the SAME active-diagnosis loop, no second onboarding system."""

    def _ev(self, session, event_id, failed, pattern, recurrence):
        session.observe(
            {
                "timestamp": "2026-08-17T22:10:00+05:30",
                "event_id": event_id,
                "concept": "binary_search",
                "secondary_concepts": ["boundary_handling"],
                "test_results": {"passed": ["normal_asc"], "failed": failed},
                "failure_classes": failed,
                "static_pattern": pattern,
                "recurrence": recurrence,
                "code": "while low < high: low = mid",
            }
        )

    def test_zero_history_thin_evidence_abstains(self):
        pack = get_pack("DSA")
        session = AdaptiveSession(pack)
        session.start_session("CS-01")
        self._ev(session, "cs-1", ["single_element"], "off_by_one_bound", False)
        snap = session.diagnose()
        outcome = session.decide(snap)
        self.assertEqual(outcome.decision, "abstain")
        self.assertIsNone(session.current_gap())

    def test_recurrence_converges_without_a_special_mode(self):
        pack = get_pack("DSA")
        session = AdaptiveSession(pack)
        session.start_session("CS-02")
        self._ev(session, "cs-2", ["left_boundary", "single_element"], "low_mid_no_increment", True)
        q = session.engine.select_question(session.diagnose().hyps, pack.questions("diagnostic"))
        best = max(range(len(q.options)), key=lambda i: q.likelihood["mc_boundary_update"][i])
        snap = session.answer_diagnostic(q, best)
        outcome = session.decide(snap)
        self.assertEqual(outcome.decision, "teach")
        gap = session.current_gap()
        self.assertIsNotNone(gap)


if __name__ == "__main__":
    unittest.main()