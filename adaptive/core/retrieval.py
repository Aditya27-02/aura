from __future__ import annotations

import re
import time
from typing import Iterable, Optional

from adaptive.core.learner_state import LearnerStateEngine
from adaptive.types import Chunk, EvidenceBundle

_LEVEL_MAP = {"foundation": 0, "easy": 1, "medium": 2, "hard": 3, "transfer": 4}


class RetrievalEngine:
    """Constrained retrieval: subject filter -> concept neighborhood -> metadata filter -> lexical score."""

    def __init__(self, corpus: Iterable[Chunk]) -> None:
        self.corpus = list(corpus)

    def _tokenize(self, text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9_]+", text.lower()))

    def _score(self, query: str, chunk: Chunk) -> float:
        qt = self._tokenize(query)
        ct = self._tokenize(chunk.text)
        if not qt:
            return 0.0
        overlap = len(qt & ct)
        if overlap == 0:
            return 0.0
        topical = 1.2 if any(t in chunk.topic.lower() for t in qt) else 1.0
        return (overlap / len(qt)) * topical * min(1.0, len(ct) / 120.0)

    def _difficulty_multiplier(self, chunk: Chunk, level: float) -> float:
        band = _LEVEL_MAP.get(chunk.difficulty_band, 2)
        diff = abs(band - int(round(level * 4)))
        if diff == 0:
            return 1.0
        if diff == 1:
            return 0.85
        return 0.6

    def retrieve(
        self,
        subject: str,
        concepts: Optional[Iterable[str]],
        query: str,
        learner_state: Optional[LearnerStateEngine] = None,
        k: int = 4,
        difficulty_adaptive: bool = True,
    ) -> EvidenceBundle:
        start = time.perf_counter()
        concepts = set(concepts) if concepts else None
        scored: list[tuple[float, Chunk]] = []
        for c in self.corpus:
            if c.subject != subject:
                continue
            if concepts and not (set(c.concept_ids) & concepts):
                continue
            score = self._score(query, c)
            if score <= 0:
                continue
            if difficulty_adaptive and learner_state is not None:
                score *= self._difficulty_multiplier(c, learner_state.learner_level())
            scored.append((score, c))
        scored.sort(key=lambda t: t[0], reverse=True)
        tops = [c for _, c in scored[:k]]
        latency = (time.perf_counter() - start) * 1000.0
        return EvidenceBundle(chunks=tops, retrieval_latency_ms=latency)