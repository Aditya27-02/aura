from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

from adaptive.core.diagnosis import DiagnosisEngine
from adaptive.core.domain_pack import DomainPack
from adaptive.core.gaps import GapRegistry
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.core.memory import MemoryCurator
from adaptive.core.retrieval import RetrievalEngine
from adaptive.core.teaching import TeachingPolicy, Tutor
from adaptive.storage.sqlite_store import MemoryStore
from adaptive.types import CandidateResponse, DiagnosisOutcome, Event, GapHypothesis, LearningGap, Question


@dataclass
class DiagnosticSnapshot:
    target: str
    hyps: list[GapHypothesis]
    posterior_map: dict
    entropy: float
    insufficient: bool
    selected_question: Optional[Question]
    session_id: str = ""

    def top(self) -> GapHypothesis:
        return max(self.hyps, key=lambda h: h.posterior)

    def ranked(self) -> list[GapHypothesis]:
        return sorted(self.hyps, key=lambda h: h.posterior, reverse=True)

    def as_live(self) -> dict:
        return {
            "target": self.target,
            "insufficient": self.insufficient,
            "entropy": round(self.entropy, 3),
            "hypotheses": [{"id": h.concept_id, "kind": h.kind, "p": round(h.posterior, 3)} for h in self.ranked()],
            "selected_question_id": self.selected_question.id if self.selected_question else None,
        }


class AdaptiveSession:
    """The closed loop: Observe -> Update State -> Diagnose -> Ask / Teach -> Verify -> Update.

    Exposes granular steps so a demo can pause at each stage, show the live
    posterior, ask a diagnostic, and drive the transfer-verified recovery.
    """

    def __init__(self, pack: DomainPack, store=None, now: Optional[str] = None) -> None:
        self.pack = pack
        self.store = store or MemoryStore()
        self.state = LearnerStateEngine(pack.bkt_defaults, now=now)
        self.curator = MemoryCurator(pack.graph, self.state, self.store)
        self.engine = DiagnosisEngine(pack.graph, self.state, pack.signal_model)
        self.policy = TeachingPolicy()
        self.tutor = Tutor(pack.hints, self.policy)
        self.retrieval = RetrievalEngine(pack.corpus)
        self.gaps = GapRegistry()
        self.current_session_id = str(uuid.uuid4())
        self.ledger: list[Event] = []
        self.active_event: Optional[Event] = None
        self.active_hyps: list[GapHypothesis] = []
        self.gap: Optional[LearningGap] = None
        self.last_intervention_id: Optional[str] = None
        self.last_bundle = None
        self.asked_question_ids: set[str] = set()

    def start_session(self, session_key: str) -> str:
        self.current_session_id = str(uuid.uuid4())
        self.asked_question_ids.clear()
        self.store.create_session(self.current_session_id, session_key, self.pack.subject)
        return self.current_session_id

    def observe(self, raw: dict, session_id: Optional[str] = None) -> Event:
        event = self.pack.evidence_adapter(raw)
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        if not event.session_id:
            event.session_id = session_id or self.current_session_id
        patch = self.curator.ingest_event(event)
        self.store.validate_and_commit(patch)
        self.active_event = event
        self.ledger.append(event)
        return event

    def seed(self, events: list[Event]) -> None:
        for ev in events:
            if not ev.event_id:
                ev.event_id = str(uuid.uuid4())
            if not ev.session_id:
                ev.session_id = self.current_session_id
            patch = self.curator.ingest_event(ev)
            self.store.validate_and_commit(patch)
            self.ledger.append(ev)

    def diagnose(self, target: Optional[str] = None, randomize_ties: bool = False) -> DiagnosticSnapshot:
        event = self.active_event
        if event is None:
            raise ValueError("no active evidence; call observe() first")
        target = target or event.concepts[0]
        hyps = self.engine.generate_hypotheses(target, event)
        hyps = self.engine.update_from_evidence(hyps, event)
        self.active_hyps = hyps
        insuff = not self.engine.clears_confidence(hyps)
        question = None
        if not insuff and self.engine.entropy_of(hyps) > self.engine.entropy_threshold:
            question = self.engine.select_question(
                hyps,
                self.pack.questions("diagnostic"),
                exclude_ids=self.asked_question_ids,
                randomize_ties=randomize_ties,
            )
            if question:
                self.asked_question_ids.add(question.id)
        return DiagnosticSnapshot(
            target=target,
            hyps=list(hyps),
            posterior_map=self.engine.posterior_map(hyps),
            entropy=self.engine.entropy_of(hyps),
            insufficient=insuff,
            selected_question=question,
            session_id=self.current_session_id,
        )

    def answer_diagnostic(self, question: Question, option_index: int) -> DiagnosticSnapshot:
        if question and question.id:
            self.asked_question_ids.add(question.id)
        self.active_hyps = self.engine.update_from_outcome(self.active_hyps, question, option_index)
        return DiagnosticSnapshot(
            target=self.active_event.concepts[0],
            hyps=list(self.active_hyps),
            posterior_map=self.engine.posterior_map(self.active_hyps),
            entropy=self.engine.entropy_of(self.active_hyps),
            insufficient=not self.engine.clears_confidence(self.active_hyps),
            selected_question=None,
            session_id=self.current_session_id,
        )

    def decide(self, snapshot: Optional[DiagnosticSnapshot] = None) -> DiagnosisOutcome:
        snap = snapshot or self.diagnose()
        result = {
            "insufficient_evidence": snap.insufficient,
            "top_posterior": snap.top().posterior,
        }
        outcome = self.policy.decide_outcome(
            snap.target, self.active_event, snap.hyps, self.pack.graph, self.state, self.engine, result
        )
        if outcome.decision == "teach" and snap.insufficient is False:
            top = self.engine.top_hypothesis(snap.hyps)
            self.gap = self.gaps.materialize(snap.target, top, self.active_event, self.pack.graph, self.state)
            outcome.gap = self.gap
        return outcome

    def retrieve(self, target: str, query: str, k: int = 3):
        concepts = self.pack.graph.concept_neighborhood(target, depth=1)
        bundle = self.retrieval.retrieve(self.pack.subject, concepts, query, self.state, k=k)
        self.last_bundle = bundle
        return bundle

    def privacy_capsule(self, *, bundle=None) -> dict:
        """§8 minimal-context capsule as it would be sent for a remote operation.

        `dry_run=True` is always set here: this engine has no remote call, so the
        content is for the privacy inspector only and the claim stays falsifiable.
        """
        from adaptive.privacy.capsule import build_session_capsule

        sources = list(bundle.citations) if bundle is not None else None
        return build_session_capsule(self, retrieved_sources=sources)

    def teach(self, outcome: DiagnosisOutcome, target: str, bundle=None, question: Optional[Question] = None) -> CandidateResponse:
        content_target = outcome.gap.misconception_class if outcome.gap is not None else target
        response = self.tutor.teach(outcome.action, content_target, bundle, self.state, question)
        if outcome.gap is not None:
            self.last_intervention_id = f"int-{uuid.uuid4().hex[:8]}"
            self.gaps.mark_intervention_applied(outcome.gap, self.last_intervention_id)
        return response

    def close_session(self, session_key: Optional[str] = None) -> dict:
        summary = self.curator.propose_session_summary(
            self.current_session_id, self.pack.subject, self.ledger, session_key
        )
        patch = self.curator.close_session(self.current_session_id, self.pack.subject, self.ledger, session_key=session_key)
        self.store.validate_and_commit(patch)
        self.store.end_session(self.current_session_id)
        return summary.__dict__

    def current_gap(self) -> Optional[LearningGap]:
        return self.gap