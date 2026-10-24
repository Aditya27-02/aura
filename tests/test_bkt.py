import unittest

from adaptive.core.learner_state import BKT, LearnerStateEngine
from adaptive.types import BKTParams, Event, STATUS_DEVELOPING, STATUS_VERIFIED


class TestBKT(unittest.TestCase):
    def test_correct_raises_belief(self):
        p0 = 0.3
        p1 = BKT.update(p0, slip=0.1, guess=0.2, learn=0.3, correct=True)
        self.assertGreater(p1, p0)
        self.assertLessEqual(p1, 1.0)

    def test_incorrect_lowers_belief(self):
        p0 = 0.7
        p1 = BKT.update(p0, slip=0.1, guess=0.2, learn=0.3, correct=False)
        self.assertLess(p1, p0)

    def test_guessy_incorrect_penalises_less(self):
        low_guess = BKT.update(0.7, slip=0.1, guess=0.05, learn=0.3, correct=False)
        high_guess = BKT.update(0.7, slip=0.1, guess=0.5, learn=0.3, correct=False)
        self.assertGreater(high_guess, low_guess)

    def test_stronger_implication_penalises_more(self):
        # strength scales how far the belief moves toward the observed outcome;
        # for an incorrect answer a stronger implication means a bigger drop.
        full = BKT.update(0.3, 0.1, 0.2, 0.3, correct=False, strength=1.0)
        weak = BKT.update(0.3, 0.1, 0.2, 0.3, correct=False, strength=0.2)
        self.assertLess(full, weak)

    def test_bounds(self):
        for correct in (True, False):
            for _ in range(200):
                p = BKT.update(0.001, 0.1, 0.2, 0.3, correct)
                self.assertGreaterEqual(p, 0.0)
                self.assertLessEqual(p, 1.0)


def _ev(correct: bool, concepts=("c1",)) -> Event:
    return Event(
        event_id="e1", session_id="s1", timestamp="2026-08-01T10:00:00+05:30",
        subject="T", concepts=list(concepts), activity="answered", input_mode="text",
        evaluation={"correct": correct}, evidence={},
    )


class TestLearnerStateEngine(unittest.TestCase):
    def setUp(self):
        self.params = {"c1": BKTParams(prior=0.3, slip=0.1, guess=0.2, learn=0.3)}
        self.engine = LearnerStateEngine(self.params)

    def test_state_initialised_from_prior(self):
        st = self.engine.state("c1")
        self.assertEqual(st.mastery_belief, 0.3)
        self.assertEqual(st.evidence_count, 0)
        self.assertEqual(st.current_status, "needs_review")

    def test_apply_updates_belief_and_count(self):
        self.engine.apply(_ev(True))
        st = self.engine.state("c1")
        self.assertEqual(st.evidence_count, 1)
        self.assertGreater(st.mastery_belief, 0.3)
        for _ in range(6):
            self.engine.apply(_ev(True))
        st = self.engine.state("c1")
        self.assertEqual(st.current_status, STATUS_VERIFIED)

    def test_secondary_concept_gets_weaker_penalty(self):
        # incorrect primary concept takes the full-strength hit;
        # secondary concepts move less.
        self.engine.apply(_ev(False, concepts=("c1", "c2")))
        primary = self.engine.state("c1")
        secondary = self.engine.state("c2")
        self.assertGreater(secondary.mastery_belief, primary.mastery_belief)


if __name__ == "__main__":
    unittest.main()