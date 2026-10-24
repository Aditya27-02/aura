from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

MASTERY_VERIFIED = 0.75
MASTERY_DEVELOPING = 0.45
EVIDENCE_HIGH = 8
EVIDENCE_MEDIUM = 3

STATUS_STALE = "stale"
STATUS_VERIFIED = "verified"
STATUS_DEVELOPING = "developing"
STATUS_NEEDS_REVIEW = "needs_review"
STATUS_ACTIVE_BLOCKER = "active_blocker"

GAP_CANDIDATE = "candidate"
GAP_ACTIVE_BLOCKER = "active_blocker"
GAP_INTERVENTION_APPLIED = "intervention_applied"
GAP_RECOVERED_PENDING_TRANSFER = "recovered_pending_transfer"
GAP_RECOVERED = "recovered"
GAP_STALE_REASSESS = "stale_reassess"

GAP_STATUSES = (
    GAP_CANDIDATE,
    GAP_ACTIVE_BLOCKER,
    GAP_INTERVENTION_APPLIED,
    GAP_RECOVERED_PENDING_TRANSFER,
    GAP_RECOVERED,
    GAP_STALE_REASSESS,
)


@dataclass
class BKTParams:
    prior: float = 0.30
    slip: float = 0.10
    guess: float = 0.20
    learn: float = 0.25


@dataclass
class ConceptState:
    concept_id: str
    mastery_belief: float
    state_confidence: float
    last_observed_at: Optional[str] = None
    evidence_count: int = 0
    current_status: str = STATUS_NEEDS_REVIEW
    recurrence_count: int = 0
    active_gap_state: Optional[str] = None
    recovery_state: Optional[str] = None

    def as_visible(self) -> dict:
        return {
            "concept_id": self.concept_id,
            "status": self.current_status,
            "active_gap_state": self.active_gap_state,
            "recovery_state": self.recovery_state,
            "last_observed_at": self.last_observed_at,
        }


@dataclass
class Event:
    event_id: str
    session_id: str
    timestamp: str
    subject: str
    concepts: list[str]
    activity: str
    input_mode: str
    response: Any = None
    evaluation: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)
    intervention_id: Optional[str] = None
    outcome: Optional[str] = None


@dataclass
class GapHypothesis:
    concept_id: str
    kind: str
    prior: float
    posterior: float
    evidence_links: list[str] = field(default_factory=list)
    recurrence_count: int = 0


@dataclass
class Question:
    id: str
    concept_id: str
    kind: str
    prompt: str
    options: list[str]
    correct_index: Optional[int] = None
    cost: float = 1.0
    likelihood: dict[str, list[float]] = field(default_factory=dict)
    distractors: dict[str, str] = field(default_factory=dict)
    answer_key_source: Optional[str] = None


@dataclass
class Chunk:
    chunk_id: str
    source_id: str
    subject: str
    topic: str
    concept_ids: list[str]
    content_type: str
    text: str
    difficulty_band: str = "medium"
    prerequisite_ids: list[str] = field(default_factory=list)
    citation_location: Optional[str] = None


@dataclass
class EvidenceBundle:
    chunks: list[Chunk] = field(default_factory=list)
    retrieval_latency_ms: float = 0.0

    @property
    def citations(self) -> list[str]:
        return [c.source_id for c in self.chunks]


@dataclass
class CandidateResponse:
    action: str
    message: str
    next_check: Optional[str] = None
    citations: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


@dataclass
class SessionSummary:
    session_id: str
    session_key: str
    subject: str
    concepts: list[str]
    started_at: str
    ended_at: str
    evidence_count: int
    gaps_strengthened: list[str] = field(default_factory=list)
    gaps_weakened: list[str] = field(default_factory=list)
    interventions_used: list[str] = field(default_factory=list)
    outcome: str = "in_progress"
    pending_next_action: Optional[str] = None


@dataclass
class MemoryPatch:
    session_id: str
    concept_state_updates: dict[str, ConceptState] = field(default_factory=dict)
    gap_hypothesis_updates: dict[str, GapHypothesis] = field(default_factory=dict)
    gap_updates: dict[str, LearningGap] = field(default_factory=dict)
    new_events: list[Event] = field(default_factory=list)
    new_summary: Optional[SessionSummary] = None
    compacted_history: list[dict] = field(default_factory=list)


@dataclass
class GoldScenario:
    id: str
    subject: str
    target_concept: str
    name: str
    seed_history: list[Event]
    current_evidence: Event
    true_gap_label: Optional[str] = None
    valid_diagnostics: list[str] = field(default_factory=list)
    acceptable_interventions: list[str] = field(default_factory=list)
    unacceptable_interventions: list[str] = field(default_factory=list)
    expected_bkt_direction: Optional[str] = None
    expects_abstention: bool = False


@dataclass
class LearningGap:
    """First-class gap primitive (AURA section 6).

    A gap is never 'recovered' until transfer_verified is true.
    """

    gap_id: str
    concept_id: str
    misconception_class: str
    hypothesis_probability: float
    evidence_count: int
    recurrence_count: int
    prerequisites_affected: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    first_detected: Optional[str] = None
    last_confirmed: Optional[str] = None
    status: str = GAP_CANDIDATE
    intervention_ids: list[str] = field(default_factory=list)
    reassessment_result: Optional[dict] = None
    transfer_verified: bool = False
    recovery_confidence: float = 0.0


@dataclass
class TransferCheck:
    transfer_problem_id: str
    concept_id: str
    original_problem_id: Optional[str]
    prompt: str
    structurally_different: bool = True
    passed: Optional[bool] = None
    submitted_at: Optional[str] = None
    evaluation_note: str = ""


@dataclass
class DiagnosisOutcome:
    """Result of the diagnosis decision point: teach a specific gap or abstain."""

    decision: str  # "teach" | "abstain"
    action: Optional[str] = None
    gap: Optional[LearningGap] = None
    reason: str = ""
    insufficiency_cause: str = ""
