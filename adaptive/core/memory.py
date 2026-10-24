from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from adaptive.core.curriculum_graph import CurriculumGraph
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.types import ConceptState, Event, GapHypothesis, MemoryPatch, SessionSummary


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryCurator:
    """The only logical role allowed to propose persistent learner-memory changes.

    Proposals are structured; application logic validates and commits them
    transactionally (validate_and_commit). One writer, deterministic commits.
    """

    def __init__(self, graph: CurriculumGraph, state_engine: LearnerStateEngine, store) -> None:
        self.graph = graph
        self.state = state_engine
        self.store = store

    def ingest_event(self, event: Event) -> MemoryPatch:
        patch = MemoryPatch(session_id=event.session_id)
        patch.new_events.append(event)

        for st in self.state.apply(event):
            patch.concept_state_updates[st.concept_id] = st

        self._detect_recurrence(event, patch)
        self._update_gap_hypotheses(event, patch)
        return patch

    def _detect_recurrence(self, event: Event, patch: MemoryPatch) -> None:
        marker = self._recurrence_marker(event)
        if marker is None:
            return
        prior = self.store.count_pattern(marker, exclude_event=event.event_id)
        if prior > 0:
            for cid in event.concepts:
                prev = patch.concept_state_updates.get(cid)
                if prev is None:
                    prev = self.state.state(cid)
                new_st = ConceptState(
                    concept_id=cid,
                    mastery_belief=prev.mastery_belief,
                    state_confidence=prev.state_confidence,
                    last_observed_at=prev.last_observed_at,
                    evidence_count=prev.evidence_count,
                    current_status=prev.current_status,
                    recurrence_count=prev.recurrence_count + 1,
                    active_gap_state="recurring",
                    recovery_state=prev.recovery_state,
                )
                patch.concept_state_updates[cid] = new_st

    def _recurrence_marker(self, event: Event) -> Optional[str]:
        if "distractor_pattern" in event.evidence:
            return str(event.evidence["distractor_pattern"])
        if "pattern" in event.evidence:
            return str(event.evidence["pattern"])
        if event.evaluation.get("failure_classes"):
            fcs = event.evaluation["failure_classes"]
            if fcs:
                return f"failure:{sorted(fcs)[0]}"
        return None

    def _update_gap_hypotheses(self, event: Event, patch: MemoryPatch) -> None:
        target = event.concepts[0]
        evidence_ids = [event.event_id]
        for key, value in event.evidence.items():
            if not isinstance(value, (str, bool)):
                continue
            gap = value if isinstance(value, str) else key
            if not gap or gap in ("recurrence", "concept_strengths", "implementation_evidence"):
                continue
            hid = f"{target}:{gap}"
            current = self.store.get_gap_hypothesis(hid)
            strength = 1.0
            posterior = (current.posterior if current else 0.3) * (1.5 if gap in event.evidence.get("what", {}) else 1.0)
            posterior = min(posterior * 1.4, 0.99)
            patch.gap_hypothesis_updates[hid] = GapHypothesis(
                concept_id=gap,
                kind="misconception",
                prior=current.prior if current else 0.3,
                posterior=posterior,
                evidence_links=(current.evidence_links if current else []) + evidence_ids,
                recurrence_count=(current.recurrence_count if current else 0) + (1 if event.evidence.get("recurrence") else 0),
            )

    def propose_session_summary(self, session_id: str, subject: str, events: list[Event], session_key: Optional[str] = None) -> SessionSummary:
        concepts = sorted({c for e in events for c in e.concepts})
        strengthened = [c for c in concepts if self.state.state(c).mastery_belief >= 0.6]
        weakened = [c for c in concepts if self.state.state(c).mastery_belief < 0.45]
        interventions = list({e.intervention_id for e in events if e.intervention_id})
        outcomes = {e.outcome for e in events if e.outcome}
        if not events:
            completed = "in_progress"
        elif "failed" in outcomes:
            completed = "needs_followup"
        elif "passed" in outcomes or all(o == "learning" for o in outcomes):
            completed = "progressing"
        else:
            completed = "in_progress"
        summary = SessionSummary(
            session_id=session_id,
            session_key=session_key or session_id[:8],
            subject=subject,
            concepts=concepts,
            started_at=events[0].timestamp if events else _iso_now(),
            ended_at=events[-1].timestamp if events else _iso_now(),
            evidence_count=len(events),
            gaps_strengthened=strengthened,
            gaps_weakened=weakened,
            interventions_used=interventions,
            outcome=completed,
        )
        return summary

    def close_session(self, session_id: str, subject: str, events: list[Event], patch: Optional[MemoryPatch] = None, session_key: Optional[str] = None) -> MemoryPatch:
        patch = patch or MemoryPatch(session_id=session_id)
        patch.new_summary = self.propose_session_summary(session_id, subject, events, session_key)
        return patch

    def compact_subject(self, subject: str, keep_recent: int = 20) -> list[dict]:
        raw = self.store.query_events(subject=subject)
        summaries = self.store.get_summaries(subject)
        if len(raw) <= keep_recent and not summaries:
            return []
        compact = {
            "subject": subject,
            "source_session_ids": list({e.session_id for e in raw}),
            "event_count": len(raw),
            "summary_count": len(summaries),
            "concepts_touched": sorted({c for e in raw for c in e.concepts}),
            "period": [raw[0].timestamp, raw[-1].timestamp] if raw else [],
        }
        return [compact]