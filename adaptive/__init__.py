from __future__ import annotations

"""Adaptive Learning Diagnosis + Personalized Companion.

A privacy-first adaptive learning system that estimates a learner's evolving
knowledge state from multimodal and task-specific evidence, identifies the
most strongly supported blocking gaps, actively asks diagnostic questions when
uncertain, teaches only when the gap is sufficiently supported, verifies the
intervention, and updates the learner model over time.

Core loop:

    Observe -> Update State -> Diagnose -> Ask / Teach -> Verify -> Update

Implementation status: Phase 0-2 of the build plan (measurement first, local
data core, learner state + diagnosis) with DSA and Biology domain packs, an
evaluation harness with calibration logging (§7.5), a §8 privacy-capsule
inspector, cold start as the same loop (§7.6), and transfer-verified recovery.
Local SLM / supervisor / QLoRA / mobile surfaces are later phases; the
deterministic teaching policy here is the interface the adapted SLM will slot
into.
"""

__version__ = "0.1.0"

from adaptive.types import (  # noqa: E402
    BKTParams,
    CandidateResponse,
    Chunk,
    ConceptState,
    DiagnosisOutcome,
    Event,
    EvidenceBundle,
    GapHypothesis,
    GoldScenario,
    LearningGap,
    MemoryPatch,
    Question,
    SessionSummary,
    TransferCheck,
    GAP_ACTIVE_BLOCKER,
    GAP_CANDIDATE,
    GAP_INTERVENTION_APPLIED,
    GAP_RECOVERED,
    GAP_RECOVERED_PENDING_TRANSFER,
    GAP_STALE_REASSESS,
)
from adaptive.core.curriculum_graph import ConceptNode, CurriculumGraph, Edge  # noqa: E402
from adaptive.core.learner_state import LearnerStateEngine  # noqa: E402
from adaptive.core.diagnosis import DiagnosisEngine  # noqa: E402
from adaptive.core.retrieval import RetrievalEngine  # noqa: E402
from adaptive.core.domain_pack import DomainPack  # noqa: E402
from adaptive.core.memory import MemoryCurator  # noqa: E402
from adaptive.core.teaching import TeachingPolicy, Tutor  # noqa: E402
from adaptive.privacy.capsule import PRIVACY_CLAIM, build_capsule, build_session_capsule  # noqa: E402

__all__ = [
    "__version__",
    "BKTParams",
    "CandidateResponse",
    "Chunk",
    "ConceptState",
    "DiagnosisOutcome",
    "Event",
    "EvidenceBundle",
    "GapHypothesis",
    "GoldScenario",
    "LearningGap",
    "MemoryPatch",
    "Question",
    "SessionSummary",
    "TransferCheck",
    "GAP_ACTIVE_BLOCKER",
    "GAP_CANDIDATE",
    "GAP_INTERVENTION_APPLIED",
    "GAP_RECOVERED",
    "GAP_RECOVERED_PENDING_TRANSFER",
    "GAP_STALE_REASSESS",
    "ConceptNode",
    "CurriculumGraph",
    "Edge",
    "LearnerStateEngine",
    "DiagnosisEngine",
    "RetrievalEngine",
    "DomainPack",
    "MemoryCurator",
    "TeachingPolicy",
    "Tutor",
    "PRIVACY_CLAIM",
    "build_capsule",
    "build_session_capsule",
]
