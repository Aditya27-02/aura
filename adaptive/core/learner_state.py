from __future__ import annotations

from adaptive.types import (
    BKTParams,
    ConceptState,
    Event,
    EVIDENCE_HIGH,
    EVIDENCE_MEDIUM,
    MASTERY_DEVELOPING,
    MASTERY_VERIFIED,
    STATUS_DEVELOPING,
    STATUS_NEEDS_REVIEW,
    STATUS_STALE,
    STATUS_VERIFIED,
)

DEFAULT_STRENGTHS = [1.0, 0.35, 0.2, 0.15, 0.1]


class BKT:
    """Bayesian Knowledge Tracing baseline.

    p_t = P(K_t = 1) for a concept.
    Correct response is modelled as:

        P(K_t=1 | C) = p(1-s) / (p(1-s) + (1-p)g)
        P(K_t=1 | I) = p s    / (p s    + (1-p)(1-g))

    followed by the learning transition p_{t+1} = p + (1 - p) t.
    """

    @staticmethod
    def update(p: float, slip: float, guess: float, learn: float, correct: bool, strength: float = 1.0) -> float:
        p = min(max(p, 1e-6), 1.0 - 1e-6)
        if correct:
            denom = p * (1 - slip) + (1 - p) * guess
            p_obs = p * (1 - slip) / denom if denom > 0 else p
        else:
            denom = p * slip + (1 - p) * (1 - guess)
            p_obs = p * slip / denom if denom > 0 else p
        p_obs = p + (p_obs - p) * strength
        p_next = p_obs + (1 - p_obs) * learn
        return min(max(p_next, 0.0), 1.0)


def _confidence_from_count(count: int) -> str:
    if count >= EVIDENCE_HIGH:
        return "high"
    if count >= EVIDENCE_MEDIUM:
        return "medium"
    return "low"


def _status_from(belief: float, count: int, stale: bool) -> str:
    if stale:
        return STATUS_STALE
    if belief >= MASTERY_VERIFIED and count >= EVIDENCE_MEDIUM:
        return STATUS_VERIFIED
    if belief >= MASTERY_DEVELOPING:
        return STATUS_DEVELOPING
    return STATUS_NEEDS_REVIEW


class LearnerStateEngine:
    """Deterministic owner of per-concept learner state (B_u overlay)."""

    def __init__(self, params: dict[str, BKTParams], now=None) -> None:
        self.params = params
        self.now = now or _iso_now()
        self.states: dict[str, ConceptState] = {}

    def params_for(self, concept_id: str) -> BKTParams:
        return self.params.get(concept_id, BKTParams())

    def state(self, concept_id: str) -> ConceptState:
        st = self.states.get(concept_id)
        if st is None:
            p = self.params_for(concept_id)
            st = ConceptState(
                concept_id=concept_id,
                mastery_belief=p.prior,
                state_confidence="low",
                evidence_count=0,
            )
        return st

    def set_state(self, state: ConceptState) -> None:
        self.states[state.concept_id] = state

    def apply(self, event: Event, now: str | None = None) -> list[ConceptState]:
        """Update BKT belief for every concept referenced by an event.

        Primary concept gets a full-strength update; secondary concepts weaker
        (multi-concept evidence is not treated as perfectly identifying any
        single latent concept).
        """
        now = now or self.now
        correct = event.evaluation.get("correct")
        if correct is None:
            return []
        strengths = event.evidence.get("concept_strengths", DEFAULT_STRENGTHS)
        updated: list[ConceptState] = []
        for i, cid in enumerate(event.concepts):
            strength = strengths[i] if i < len(strengths) else 0.1
            if strength <= 0:
                continue
            st = self.state(cid)
            p = st.mastery_belief
            p_v = self.params_for(cid)
            p_new = BKT.update(p, p_v.slip, p_v.guess, p_v.learn, correct, strength)
            count = st.evidence_count + 1
            stale = False
            new_st = ConceptState(
                concept_id=cid,
                mastery_belief=p_new,
                state_confidence=_confidence_from_count(count),
                last_observed_at=now,
                evidence_count=count,
                current_status=_status_from(p_new, count, stale),
                recurrence_count=st.recurrence_count,
                active_gap_state=st.active_gap_state,
                recovery_state=st.recovery_state,
            )
            self.set_state(new_st)
            updated.append(new_st)
        return updated

    def mark_stale(self, cid: str, stale: bool) -> ConceptState:
        st = self.state(cid)
        if stale and st.current_status == STATUS_VERIFIED:
            new_st = ConceptState(
                concept_id=cid,
                mastery_belief=st.mastery_belief,
                state_confidence=st.state_confidence,
                last_observed_at=st.last_observed_at,
                evidence_count=st.evidence_count,
                current_status=STATUS_STALE,
                recurrence_count=st.recurrence_count,
                active_gap_state=st.active_gap_state,
                recovery_state=st.recovery_state,
            )
            self.set_state(new_st)
            return new_st
        return st

    def recurrence_for(self, cid: str) -> int:
        return self.state(cid).recurrence_count

    def bump_recurrence(self, cid: str) -> ConceptState:
        st = self.state(cid)
        new_st = ConceptState(
            concept_id=cid,
            mastery_belief=st.mastery_belief,
            state_confidence=st.state_confidence,
            last_observed_at=st.last_observed_at,
            evidence_count=st.evidence_count,
            current_status=st.current_status,
            recurrence_count=st.recurrence_count + 1,
            active_gap_state=st.active_gap_state,
            recovery_state=st.recovery_state,
        )
        self.set_state(new_st)
        return new_st

    def learner_level(self) -> float:
        states = [s for s in self.states.values() if s.evidence_count > 0]
        if not states:
            return 0.0
        return sum(s.mastery_belief for s in states) / len(states)

    def to_dict(self) -> dict[str, dict]:
        return {cid: _state_to_dict(s) for cid, s in self.states.items()}


def _state_to_dict(s: ConceptState) -> dict:
    return {
        "mastery_belief": s.mastery_belief,
        "state_confidence": s.state_confidence,
        "evidence_count": s.evidence_count,
        "last_observed_at": s.last_observed_at,
        "current_status": s.current_status,
        "recurrence_count": s.recurrence_count,
        "active_gap_state": s.active_gap_state,
        "recovery_state": s.recovery_state,
    }


def _iso_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()