from __future__ import annotations

from typing import Optional

from adaptive.core.curriculum_graph import CurriculumGraph
from adaptive.core.diagnosis import HYP_IMPLEMENTATION, HYP_MISCONCEPTION, HYP_PRE_REQ, DiagnosisEngine
from adaptive.core.learner_state import LearnerStateEngine, STATUS_STALE
from adaptive.types import CandidateResponse, DiagnosisOutcome, Event, GapHypothesis, Question

ACTION_DIAGNOSTIC = "DIAGNOSTIC"
ACTION_PREREQ_REWIND = "PREREQUISITE_REWIND"
ACTION_CONTRASTIVE = "CONTRASTIVE_EXPLANATION"
ACTION_HINT = "HINT"
ACTION_EXPLAIN = "EXPLAIN"
ACTION_REASSESS = "REASSESS"
ACTION_PRACTICE = "PRACTICE"


class TeachingPolicy:
    """Decide the next learning action from the diagnosis state (section 22)."""

    def decide(
        self,
        target: str,
        event: Event,
        hyps: list[GapHypothesis],
        graph: CurriculumGraph,
        state: LearnerStateEngine,
        engine: DiagnosisEngine,
    ) -> tuple[str, str]:
        if not hyps:
            return ACTION_DIAGNOSTIC, "no candidate blocking hypothesis could be built"

        uncertain = engine.entropy_of(hyps) > engine.entropy_threshold
        top = engine.top_hypothesis(hyps)
        st = state.state(target)

        if st.current_status == STATUS_STALE and st.evidence_count > 0:
            return ACTION_REASSESS, "state is stale; a short reassessment beats re-explaining"

        if not engine.clears_confidence(hyps):
            return ACTION_DIAGNOSTIC, "support is insufficient; ask one more diagnostic or escalate before teaching"

        if uncertain and top.posterior < engine.confidence_threshold:
            return ACTION_DIAGNOSTIC, "evidence cannot disambiguate the blocking hypothesis yet"

        if top.kind == HYP_PRE_REQ:
            if state.state(top.concept_id).current_status in ("verified", "developing"):
                return ACTION_HINT, "prerequisite is strong enough; the failure is more likely an implementation slip"
            return ACTION_PREREQ_REWIND, f"missing prerequisite: {top.concept_id} is the most supported blocker"

        if top.kind == HYP_MISCONCEPTION:
            if top.recurrence_count >= 1 or event.evidence.get("recurrence"):
                return ACTION_CONTRASTIVE, f"recurring misconception: {top.concept_id}"
            return ACTION_EXPLAIN, f"misconception supported but not recurrent: {top.concept_id}"

        if top.kind == HYP_IMPLEMENTATION:
            return ACTION_HINT, "concept understood but implementation is losing its invariant"

        return ACTION_EXPLAIN, "fallback: introduce the concept with evidence grounding"

    def decide_outcome(
        self,
        target: str,
        event: Event,
        hyps: list[GapHypothesis],
        graph: CurriculumGraph,
        state: LearnerStateEngine,
        engine: DiagnosisEngine,
        result: Optional[dict] = None,
    ) -> DiagnosisOutcome:
        """Decision point with an explicit abstention state (AURA 7.3)."""
        if result is not None and result.get("insufficient_evidence"):
            return DiagnosisOutcome(
                decision="abstain",
                reason="no hypothesis cleared the confidence threshold after available diagnostics",
                insufficiency_cause="max_posterior_below_threshold",
            )
        if not hyps:
            return DiagnosisOutcome(decision="abstain", reason="no candidate hypotheses", insufficiency_cause="no_hypotheses")
        if not engine.clears_confidence(hyps) and engine.entropy_of(hyps) > engine.entropy_threshold:
            return DiagnosisOutcome(
                decision="abstain",
                reason="ambiguity remains; request one more diagnostic or escalate",
                insufficiency_cause="high_uncertainty",
            )
        action, rationale = self.decide(target, event, hyps, graph, state, engine)
        return DiagnosisOutcome(decision="teach", action=action, reason=rationale)


class Tutor:
    """Deterministic teaching surface.

    This is the slot the QLoRA-adapted local SLM fills in later phases; for the
    core demo it answers from each domain's hint bank and retrieved evidence so
    the loop is complete and testable end to end.
    """

    def __init__(self, hints: dict, policy: TeachingPolicy) -> None:
        self.hints = hints
        self.policy = policy

    def teach(
        self,
        action: str,
        target: str,
        bundle=None,
        learner_state: Optional[LearnerStateEngine] = None,
        question: Optional[Question] = None,
    ) -> CandidateResponse:
        bucket = self.hints.get(action, {})
        message = bucket.get(target) or bucket.get("_default")
        if message is None:
            message = self._generic(action, target)

        meta = {"action": action, "target": target}
        next_check = None
        if action == ACTION_HINT:
            next_check = "Try the boundary case where the remaining interval has length one."
        elif action == ACTION_PREREQ_REWIND:
            next_check = "Could you restate the invariant that must hold at the start of each loop iteration?"
        elif action == ACTION_CONTRASTIVE:
            next_check = "One discriminative follow-up will confirm whether the distinction stuck."
        elif action == ACTION_DIAGNOSTIC and question is not None:
            meta["question"] = {"id": question.id, "prompt": question.prompt, "options": question.options}

        citations = list(getattr(bundle, "citations", []) or [])
        return CandidateResponse(action=action, message=message, next_check=next_check, citations=citations, meta=meta)

    def _generic(self, action: str, target: str) -> str:
        if action == ACTION_HINT:
            return f"Focus your next attempt on {target} without jumping to the full solution."
        if action == ACTION_PREREQ_REWIND:
            return f"Let us quickly revisit the prerequisite idea behind {target} before continuing."
        if action == ACTION_CONTRASTIVE:
            return f"Here is a short distinction focused on {target}."
        return f"Let us work on {target} together."