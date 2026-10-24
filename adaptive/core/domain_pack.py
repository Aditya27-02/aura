from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from adaptive.core.curriculum_graph import CurriculumGraph
from adaptive.core.diagnosis import SignalModel
from adaptive.core.learner_state import BKTParams
from adaptive.types import Chunk, Question

EvidenceAdapter = Callable[..., object]


@dataclass
class TeachingPolicyDefinition:
    action: str
    rationale: str
    payload: Optional[dict] = None


@dataclass
class DomainPack:
    """One learning engine, different evidence adapters.

    For the hackathon the packs are DSA (executable evidence) and Biology
    (trusted theory evidence).
    """

    name: str
    subject: str
    version: str
    graph: CurriculumGraph
    signal_model: SignalModel
    items: list[Question]
    corpus: list[Chunk]
    bkt_defaults: dict[str, BKTParams]
    evidence_adapter: EvidenceAdapter
    hints: dict = field(default_factory=dict)
    teaching_policy: TeachingPolicyDefinition = None  # type: ignore[assignment]

    def questions(self, kind: Optional[str] = None) -> list[Question]:
        if kind is None:
            return list(self.items)
        return [q for q in self.items if q.kind == kind]