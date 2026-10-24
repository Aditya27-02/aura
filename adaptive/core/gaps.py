from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from adaptive.core.diagnosis import DiagnosisEngine
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.types import (
    GAP_ACTIVE_BLOCKER,
    GAP_CANDIDATE,
    GAP_INTERVENTION_APPLIED,
    GAP_RECOVERED,
    GAP_RECOVERED_PENDING_TRANSFER,
    GAP_STALE_REASSESS,
    Event,
    GapHypothesis,
    LearningGap,
    Question,
    TransferCheck,
)

RECOVERY_CONFIDENCE_HIGH = 0.80


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def gap_key(target: str, misconception_class: str) -> str:
    return f"{target}:{misconception_class}"


class GapRegistry:
    """Owns the LearningGap lifecycle.

    status transitions:

        candidate -> active_blocker (evidence clears confidence)
        active_blocker -> intervention_applied (intervention delivered)
        intervention_applied -> recovered_pending_transfer (original passes)
        recovered_pending_transfer -> recovered (transfer problem passes)
        recovered_pending_transfer -> active_blocker (transfer fails)
        any -> stale_reassess (stale)
    """

    def __init__(self) -> None:
        self.gaps: dict[str, LearningGap] = {}

    def get(self, target: str, misconception_class: str) -> Optional[LearningGap]:
        return self.gaps.get(gap_key(target, misconception_class))

    def get_by_id(self, gap_id: str) -> Optional[LearningGap]:
        for g in self.gaps.values():
            if g.gap_id == gap_id:
                return g
        return None

    def materialize(
        self,
        target: str,
        hypothesis: GapHypothesis,
        evidence: Event,
        graph,
        state: LearnerStateEngine,
        now: Optional[str] = None,
    ) -> LearningGap:
        """Promote the strongest hypothesis into a first-class LearningGap."""
        now = now or _iso_now()
        existing = self.get(target, hypothesis.concept_id)
        predecessors = graph.prerequisites(target)
        if existing is None:
            gap = LearningGap(
                gap_id=str(uuid.uuid4()),
                concept_id=target,
                misconception_class=hypothesis.concept_id,
                hypothesis_probability=hypothesis.posterior,
                evidence_count=1,
                recurrence_count=state.recurrence_for(hypothesis.concept_id),
                prerequisites_affected=predecessors,
                evidence_ids=[evidence.event_id] if evidence.event_id else [],
                first_detected=now,
                last_confirmed=now,
                status=(
                    GAP_ACTIVE_BLOCKER
                    if hypothesis.posterior >= 0.6
                    else GAP_CANDIDATE
                ),
            )
            self.gaps[gap_key(target, hypothesis.concept_id)] = gap
            return gap
        existing.evidence_count += 1
        existing.hypothesis_probability = hypothesis.posterior
        existing.last_confirmed = now
        if evidence.event_id:
            existing.evidence_ids.append(evidence.event_id)
        if hypothesis.posterior >= 0.6 and existing.status == GAP_CANDIDATE:
            existing.status = GAP_ACTIVE_BLOCKER
        return existing

    def mark_intervention_applied(self, gap: LearningGap, intervention_id: str, now: Optional[str] = None) -> LearningGap:
        if intervention_id not in gap.intervention_ids:
            gap.intervention_ids.append(intervention_id)
        if gap.status in (GAP_ACTIVE_BLOCKER, GAP_CANDIDATE):
            gap.status = GAP_INTERVENTION_APPLIED
        return gap

    def mark_original_recovered(self, gap: LearningGap, reassessment_result: dict, now: Optional[str] = None) -> LearningGap:
        """Original problem passes after the intervention: pending transfer, not recovered."""
        gap.reassessment_result = reassessment_result
        gap.status = GAP_RECOVERED_PENDING_TRANSFER
        gap.recovery_confidence = min(gap.recovery_confidence + 0.2 + 0.1 * len(gap.intervention_ids), 0.95)
        gap.last_confirmed = now or _iso_now()
        return gap

    def verify_transfer(self, gap: LearningGap, transfer_check: TransferCheck) -> LearningGap:
        """The gap is only recovered when the structurally different problem passes."""
        if transfer_check.passed is None:
            return gap
        gap.transfer_verified = bool(transfer_check.passed)
        if transfer_check.passed:
            gap.status = GAP_RECOVERED
            gap.recovery_confidence = min(
                max(gap.recovery_confidence, RECOVERY_CONFIDENCE_HIGH + 0.1 * len(gap.intervention_ids)),
                0.98,
            )
        else:
            gap.status = GAP_ACTIVE_BLOCKER
            gap.recovery_confidence = max(gap.recovery_confidence - 0.3, 0.0)
        return gap

    def mark_stale(self, gap: LearningGap, now: Optional[str] = None) -> LearningGap:
        if gap.status in (GAP_RECOVERED, GAP_ACTIVE_BLOCKER):
            gap.status = GAP_STALE_REASSESS
        return gap


def select_transfer_problem(
    items: list[Question],
    concept_id: str,
    original_problem_id: Optional[str] = None,
    exclude_ids: set[str] | None = None,
) -> Optional[Question]:
    """Pick a structurally different problem on the same concept for transfer verification."""
    exclude = set(exclude_ids) if exclude_ids else set()
    if original_problem_id:
        exclude.add(original_problem_id)

    candidates = [q for q in items if q.concept_id == concept_id and q.kind == "practice" and q.id not in exclude]
    if candidates:
        return candidates[0]

    staged = [
        q for q in items
        if q.concept_id == concept_id and q.kind in ("practice", "reassessment") and q.id not in exclude
    ]
    if staged:
        return staged[0]

    all_on_concept = [q for q in items if q.concept_id == concept_id and q.id not in exclude]
    return all_on_concept[0] if all_on_concept else (items[0] if items else None)


def make_transfer_check(
    transfer_item: Question,
    original_problem_id: Optional[str],
    passed: bool,
    note: str = "",
    submitted_at: Optional[str] = None,
) -> TransferCheck:
    return TransferCheck(
        transfer_problem_id=transfer_item.id,
        concept_id=transfer_item.concept_id,
        original_problem_id=original_problem_id,
        prompt=transfer_item.prompt,
        structurally_different=True,
        passed=passed,
        submitted_at=submitted_at or _iso_now(),
        evaluation_note=note,
    )