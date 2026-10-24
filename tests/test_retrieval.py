import unittest

from adaptive.core.retrieval import RetrievalEngine
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.domains import get_pack
from adaptive.types import Chunk


class TestRetrieval(unittest.TestCase):
    def setUp(self):
        self.pack = get_pack("DSA")
        self.engine = RetrievalEngine(self.pack.corpus)

    def test_subject_filter(self):
        bio_pack = get_pack("Biology")
        engine = RetrievalEngine(bio_pack.corpus + self.pack.corpus)
        bundle = engine.retrieve("Biology", None, "golgi packaging", k=10)
        self.assertTrue(bundle.chunks)
        self.assertTrue(all(c.subject == "Biology" for c in bundle.chunks))

    def test_concept_metadata_filter(self):
        bundle = self.engine.retrieve("DSA", ["loop_invariant"], "while loop interval", k=10)
        self.assertTrue(bundle.chunks)
        self.assertTrue(all("loop_invariant" in c.concept_ids for c in bundle.chunks))

    def test_relevance_ranking(self):
        query = "update low equals mid interval shrink"
        bundle = self.engine.retrieve("DSA", ["binary_search", "boundary_handling"], query, k=5)
        tops = bundle.chunks
        self.assertTrue(tops)
        self.assertTrue(any("mid + 1" in c.text or "mid + 1" in c.text or "strictly" in c.text for c in tops[:2]))

    def test_citations_present(self):
        bundle = self.engine.retrieve("DSA", ["binary_search"], "binary search", k=3)
        self.assertTrue(all(c.source_id for c in bundle.chunks))
        self.assertEqual(len(bundle.citations), len(bundle.chunks))

    def test_empty_returns_empty_bundle(self):
        bundle = self.engine.retrieve("DSA", ["nonexistent_concept"], "anything", k=5)
        self.assertEqual(bundle.chunks, [])


if __name__ == "__main__":
    unittest.main()