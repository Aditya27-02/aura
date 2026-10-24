from __future__ import annotations

import math
import random
from typing import Callable, Mapping, Optional

from adaptive.core.curriculum_graph import CurriculumGraph
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.types import Event, GapHypothesis, Question

HYP_PRE_REQ = "prerequisite_gap"
HYP_MISCONCEPTION = "misconception"
HYP_IMPLEMENTATION = "implementation_bug"

SIGNAL_RECURRENCE = "recurrence"

DEFAULT_LIKELIHOOD = 0.30


class SignalModel:
    """P(signal | hypothesis) table.

    mapping[hypothesis_id][signal] = P(signal | hyp) in (0, 1].
    A signal with no mapping for a hypothesis uses DEFAULT_LIKELIHOOD, so a
    supportive signal raises that hypothesis's weight relative to unrelated ones.
    """

    def __init__(self, mapping: Mapping[str, Mapping[str, float]], default: float = DEFAULT_LIKELIHOOD) -> None:
        self.mapping = {k: dict(v) for k, v in mapping.items()}
        self.default = default

    def likelihood(self, hypothesis_id: str, signal: str) -> float:
        return self.mapping.get(hypothesis_id, {}).get(signal, self.default)

    def base_prior(self, hypothesis_id: str) -> float:
        row = self.mapping.get(hypothesis_id, {})
        if "__prior__" in row:
            return float(row["__prior__"])
        return 0.25


def entropy(dist: list[float]) -> float:
    total = sum(dist)
    if total <= 0:
        return 0.0
    h = 0.0
    for p in dist:
        p = p / total
        if p > 1e-9:
            h -= p * math.log(p)
    return h


def normalize(items: list[tuple[str, float]]) -> list[tuple[str, float]]:
    total = sum(v for _, v in items)
    if total <= 0:
        n = len(items)
        return [(k, 1.0 / n) for k, _ in items]
    return [(k, v / total) for k, v in items]


def information_gain(prior: dict[str, float], question: Question) -> float:
    """Expected information gain of a diagnostic question.

        IG(q) = H(pi_t) - sum_y P(y|q) H(pi_{t+1}^{(q,y)})
    """
    hyps = [h for h in prior if h in question.likelihood]
    if not hyps:
        return 0.0
    h_prior = entropy([prior[h] for h in hyps])
    n_options = len(question.options)
    expected_h = 0.0
    for oi in range(n_options):
        p_y = 0.0
        for h in hyps:
            p_y += prior[h] * _safe(question.likelihood[h][oi], n_options, question)
        if p_y <= 1e-9:
            continue
        post = [prior[h] * _safe(question.likelihood[h][oi], n_options, question) / p_y for h in hyps]
        expected_h += p_y * entropy(post)
    return max(h_prior - expected_h, 0.0)


def _safe(value: float, n_options: int, q: Question) -> float:
    if isinstance(value, (int, float)) and 0.0 <= value <= 1.0:
        return value
    return 1.0 / n_options


class DiagnosisEngine:
    """Gap diagnosis as hypothesis inference over blocking-gap candidates."""

    def __init__(
        self,
        graph: CurriculumGraph,
        state_engine: LearnerStateEngine,
        signal_model: SignalModel,
        max_turns: int = 3,
        entropy_threshold: float = 0.55,
        confidence_threshold: float = 0.60,
    ) -> None:
        self.graph = graph
        self.state = state_engine
        self.signal_model = signal_model
        self.max_turns = max_turns
        self.entropy_threshold = entropy_threshold
        self.confidence_threshold = confidence_threshold

    def generate_hypotheses(self, target: str, event: Optional[Event] = None) -> list[GapHypothesis]:
        """Build the candidate blocking-gap hypotheses for a failing target.

        Candidates come from prerequisite closure (missing prerequisite) and the
        misconception mappings attached to the concept. The prior combines
        curriculum relevance with the learner's current belief, so a concept the
        learner already masters is less likely to be the blocker.
        """
        raw: list[tuple[str, str, float]] = []
        depth = self.graph.path_depth  # direct predecessor weights
        predecessors = self.graph.prerequisites(target)
        ancestors = self.graph.prereq_closure(target)

        rel_weight: dict[str, float] = {}
        for a in ancestors:
            d = depth(a, target)
            w = 1.0 if d == 1 else (0.7 if d == 2 else 0.45)
            rel_weight[a] = w
        for p in predecessors:
            rel_weight.setdefault(p, 1.0)

        for cid, w in rel_weight.items():
            belief = self.state.state(cid).mastery_belief
            gap_mass = 1.0 - min(belief, 0.85)
            prior = w * (0.35 + 0.65 * gap_mass)
            if self.state.recurrence_for(cid) > 0:
                prior *= 1.5
            raw.append((cid, HYP_PRE_REQ, prior))

        for mc in self.graph.misconceptions(target):
            base = self.signal_model.base_prior(mc)
            rec = self.state.recurrence_for(mc)
            prior = base * (1.4 if rec > 0 else 1.0)
            raw.append((mc, HYP_MISCONCEPTION, prior))

        if event is not None and event.evidence.get("implementation_evidence"):
            raw.append((target, HYP_IMPLEMENTATION, 0.5))

        norm = normalize([(f"{kind}:{cid}", v) for cid, kind, v in raw])
        hyps: list[GapHypothesis] = []
        for key, prob in norm:
            kind, cid = key.split(":", 1)
            hyps.append(
                GapHypothesis(
                    concept_id=cid,
                    kind=kind,
                    prior=prob,
                    posterior=prob,
                    recurrence_count=self.state.recurrence_for(cid),
                )
            )
        return hyps

    def extract_signals(self, event: Event) -> list[str]:
        signals: list[str] = []
        ev = event.evidence
        for key, value in ev.items():
            if key == "concept_strengths":
                continue
            if isinstance(value, bool) and value:
                signals.append(key)
            elif isinstance(value, str):
                signals.append(value)
            elif isinstance(value, list):
                signals.extend(s for s in value if isinstance(s, str))
        return list(dict.fromkeys(signals))

    def update_from_evidence(self, hyps: list[GapHypothesis], event: Event) -> list[GapHypothesis]:
        signals = self.extract_signals(event)
        items: list[tuple[str, float]] = []
        for h in hyps:
            lh = 1.0
            for sig in signals:
                if sig == SIGNAL_RECURRENCE and h.recurrence_count > 0:
                    lh *= 0.85
                else:
                    lh *= self.signal_model.likelihood(h.concept_id, sig)
            items.append((f"{h.kind}:{h.concept_id}", h.prior * lh))
            h.evidence_links.append(event.event_id)
        norm = normalize(items)
        for h, (_, prob) in zip(hyps, norm):
            h.posterior = prob
        return hyps

    def update_from_outcome(self, hyps: list[GapHypothesis], question: Question, outcome_index: int) -> list[GapHypothesis]:
        items: list[tuple[str, float]] = []
        n_options = len(question.options)
        for h in hyps:
            row = question.likelihood.get(h.concept_id)
            if row is None or not (0 <= outcome_index < len(row)):
                lh = 1.0 / n_options
            else:
                lh = _safe(row[outcome_index], n_options, question)
            items.append((f"{h.kind}:{h.concept_id}", h.posterior * lh))
        norm = normalize(items)
        for h, (_, prob) in zip(hyps, norm):
            h.posterior = prob
        return hyps

    def posterior_map(self, hyps: list[GapHypothesis]) -> dict[str, float]:
        return {h.concept_id: h.posterior for h in hyps}

    def entropy_of(self, hyps: list[GapHypothesis]) -> float:
        return entropy([h.posterior for h in hyps])

    def select_question(
        self,
        hyps: list[GapHypothesis],
        items: list[Question],
        cost_weight: float = 0.25,
        exclude_ids: set[str] | None = None,
        randomize_ties: bool = False,
    ) -> Optional[Question]:
        """Select q* = argmax_q (IG(q) - lambda * C(q)) over valid diagnostic items."""
        prior = self.posterior_map(hyps)
        exclude = exclude_ids or set()
        scored: list[tuple[float, Question]] = []
        for q in items:
            if q.kind != "diagnostic":
                continue
            if q.id in exclude:
                continue
            ig = information_gain(prior, q)
            if ig <= 0:
                continue
            score = ig - cost_weight * q.cost
            scored.append((score, q))

        if not scored:
            return None

        scored.sort(key=lambda x: x[0], reverse=True)
        top_score = scored[0][0]

        if randomize_ties and len(scored) > 1:
            candidates = [q for score, q in scored if score >= top_score - 0.35 or score >= top_score * 0.5]
            if len(candidates) > 1:
                import random
                return random.choice(candidates)

        return scored[0][1]

    def simulate_answer(self, question: Question, true_hypothesis_id: str | None, rng: random.Random) -> int:
        """Draw a learner answer.

        With a known true hypothesis, sample according to P(outcome | hypothesis).
        Without one (abstention cases), draw uniformly so a forced answer cannot
        manufacture confidence.
        """
        n = len(question.options)
        if true_hypothesis_id is None:
            return rng.randrange(n)
        row = question.likelihood.get(true_hypothesis_id)
        if row is None:
            return rng.randrange(n)
        probs = [_safe(v, n, question) for v in row]
        return rng.choices(range(n), weights=probs, k=1)[0]

    def top_hypothesis(self, hyps: list[GapHypothesis]) -> GapHypothesis:
        return max(hyps, key=lambda h: h.posterior)

    def clears_confidence(self, hyps: list[GapHypothesis]) -> bool:
        return self.top_hypothesis(hyps).posterior >= self.confidence_threshold

    def run_active_diagnosis(
        self,
        hyps: list[GapHypothesis],
        items: list[Question],
        true_label: Optional[str] = None,
        seed: int = 0,
        informative: bool = True,
    ) -> dict:
        """Iterate the active-diagnosis loop until confident or turns exhausted.

        informative=False models an uninformative learner whose answers carry no
        new information (e.g. abstention/ambiguous cases), so the posterior is
        not allowed to concentrate and the system stays in INSUFFICIENT EVIDENCE.

        Returns a transcript of the diagnostic session plus final statistics.
        When no hypothesis clears the confidence threshold after the loop, the
        outcome is an explicit abstention state (INSUFFICIENT EVIDENCE), never a
        forced guess.
        """
        if not informative:
            top0 = self.top_hypothesis(hyps)
            return {
                "transcript": [],
                "turns": 0,
                "stopped_early": True,
                "final_entropy": self.entropy_of(hyps),
                "top_hypothesis": top0.concept_id,
                "top_posterior": top0.posterior,
                "max_posterior": top0.posterior,
                "insufficient_evidence": not self.clears_confidence(hyps),
                "posterior_map": self.posterior_map(hyps),
            }
        rng = random.Random(seed)
        turns = []
        steps = 0
        final_entropy = self.entropy_of(hyps)
        stopped_early = False
        asked: set[str] = set()
        for _ in range(self.max_turns):
            if self.clears_confidence(hyps):
                stopped_early = True
                break
            if final_entropy <= self.entropy_threshold:
                stopped_early = True
                break
            q = self.select_question(hyps, items, exclude_ids=asked)
            if q is None:
                break
            asked.add(q.id)
            if true_label is not None:
                outcome = self.simulate_answer(q, true_label, rng)
            else:
                outcome = self.simulate_answer(q, None, rng)
            before = self.entropy_of(hyps)
            hyps = self.update_from_outcome(hyps, q, outcome)
            after = self.entropy_of(hyps)
            steps += 1
            final_entropy = after
            turns.append(
                {
                    "question_id": q.id,
                    "chosen_option": outcome,
                    "entropy_before": before,
                    "entropy_after": after,
                }
            )
        top = self.top_hypothesis(hyps)
        insufficient = not self.clears_confidence(hyps)
        return {
            "transcript": turns,
            "turns": steps,
            "stopped_early": stopped_early,
            "final_entropy": final_entropy,
            "top_hypothesis": top.concept_id,
            "top_posterior": top.posterior,
            "max_posterior": top.posterior,
            "insufficient_evidence": insufficient,
            "posterior_map": self.posterior_map(hyps),
        }