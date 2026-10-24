import unittest

from adaptive.core.memory import MemoryCurator
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.domains import get_pack
from adaptive.storage.sqlite_store import MemoryStore
from adaptive.types import Event


def _code_event(session, day, failure_classes, pattern, recurrence):
    return Event(
        event_id=f"{session}-{day}",
        session_id=session,
        timestamp=f"2026-08-{day:02d}T10:00:00+05:30",
        subject="DSA",
        concepts=["binary_search", "boundary_handling"],
        activity="code_submission",
        input_mode="code",
        evaluation={"correct": not failure_classes, "failure_classes": failure_classes},
        evidence=(
            {"pattern": pattern, "recurrence": True}
            if recurrence
            else {"pattern": pattern, "failure_classes": failure_classes}
        ),
    )


class TestMemoryCurator(unittest.TestCase):
    def setUp(self):
        self.pack = get_pack("DSA")
        self.store = MemoryStore()
        self.state = LearnerStateEngine(self.pack.bkt_defaults)
        self.curator = MemoryCurator(self.pack.graph, self.state, self.store)

    def test_recurrence_detection_across_sessions(self):
        self.store.validate_and_commit(self.curator.ingest_event(_code_event("s1", 1, ["left_boundary"], "low_mid_no_increment", True)))
        patch = self.curator.ingest_event(_code_event("s2", 2, ["left_boundary"], "low_mid_no_increment", True))
        self.store.validate_and_commit(patch)
        bs = patch.concept_state_updates["binary_search"]
        self.assertEqual(bs.recurrence_count, 1)
        self.assertEqual(bs.active_gap_state, "recurring")

    def test_event_ledger_append_only(self):
        self.store.validate_and_commit(self.curator.ingest_event(_code_event("s1", 1, ["left_boundary"], "low_mid_no_increment", False)))
        events = self.store.query_events(subject="DSA")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].evidence["pattern"], "low_mid_no_increment")

    def test_query_by_concept_and_time(self):
        self.store.validate_and_commit(self.curator.ingest_event(_code_event("s1", 1, [], "p1", False)))
        self.store.validate_and_commit(self.curator.ingest_event(_code_event("s2", 3, [], "p2", False)))
        since = "2026-08-02T00:00:00+05:30"
        events = self.store.query_events(subject="DSA", since=since)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].timestamp[:10], "2026-08-03")

    def test_session_summary(self):
        ev = _code_event("s1", 1, [], "p1", False)
        self.store.validate_and_commit(self.curator.ingest_event(ev))
        summary = self.curator.propose_session_summary("s1", "DSA", [ev], "DSA-20260801-S01")
        self.assertEqual(summary.session_key, "DSA-20260801-S01")
        self.assertIn("binary_search", summary.concepts)
        self.assertEqual(summary.evidence_count, 1)

    def test_deterministic_commit_rejects_non_patch(self):
        with self.assertRaises(TypeError):
            self.store.validate_and_commit("not-a-patch")

    def test_gap_persistence_roundtrip(self):
        self.store.validate_and_commit(self.curator.ingest_event(_code_event("s1", 1, [], "p1", False)))
        from adaptive.core.gaps import GapRegistry
        from adaptive.types import GapHypothesis

        registry = GapRegistry()
        ev = self.store.query_events(subject="DSA")[0]
        hyp = GapHypothesis("mc_boundary_update", "misconception", 0.3, 0.8)
        gap = registry.materialize("binary_search", hyp, ev, self.pack.graph, self.state)
        self.store.upsert_gap(gap)
        loaded = self.store.get_gap("binary_search", "mc_boundary_update")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, gap.status)


if __name__ == "__main__":
    unittest.main()