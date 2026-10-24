from __future__ import annotations

from adaptive.core.diagnosis import DiagnosisEngine
from adaptive.core.domain_pack import DomainPack
from adaptive.core.gaps import select_transfer_problem
from adaptive.core.learner_state import LearnerStateEngine
from adaptive.core.memory import MemoryCurator
from adaptive.core.teaching import TeachingPolicy, Tutor
from adaptive.domains import get_pack
from adaptive.evaluation.scenarios import build_scenarios
from adaptive.storage.sqlite_store import MemoryStore


class EvaluationHarness:
    """Run gold scenarios through the learner-state + diagnosis pipeline and score gap accuracy.

    Handles both blocked-gap scenarios (accuracy vs. the true gap label) and
    adversarial abstention scenarios (the system must explicitly say
    INSUFFICIENT EVIDENCE rather than force a guess).
    """

    def __init__(self, pack: DomainPack, seed: int = 7) -> None:
        self.pack = pack
        self.seed = seed
        self.policy = TeachingPolicy()
        self.tutor = Tutor(pack.hints, self.policy)
        self.calibration_log: list[dict] = []

    def _fresh(self):
        store = MemoryStore()
        state = LearnerStateEngine(self.pack.bkt_defaults)
        curator = MemoryCurator(self.pack.graph, state, store)
        engine = DiagnosisEngine(self.pack.graph, state, self.pack.signal_model)
        return store, state, curator, engine

    def run_scenario(self, scenario, active: bool = True) -> dict:
        store, state, curator, engine = self._fresh()
        for ev in scenario.seed_history:
            store.validate_and_commit(curator.ingest_event(ev))
        state.apply(scenario.current_evidence)

        hyps = engine.generate_hypotheses(scenario.target_concept, scenario.current_evidence)
        engine.update_from_evidence(hyps, scenario.current_evidence)
        initial_top = hyps[0] if hyps else None
        initial_entropy = engine.entropy_of(hyps)

        if active:
            result = engine.run_active_diagnosis(
                hyps,
                self.pack.questions("diagnostic"),
                true_label=scenario.true_gap_label,
                seed=self.seed,
                informative=not scenario.expects_abstention,
            )
        else:
            result = {
                "transcript": [],
                "turns": 0,
                "stopped_early": False,
                "final_entropy": initial_entropy,
                "top_hypothesis": initial_top.concept_id if initial_top else None,
                "top_posterior": initial_top.posterior if initial_top else 0.0,
                "max_posterior": initial_top.posterior if initial_top else 0.0,
                "insufficient_evidence": not engine.clears_confidence(hyps),
                "posterior_map": engine.posterior_map(hyps),
            }

        outcome = self.policy.decide_outcome(
            scenario.target_concept,
            scenario.current_evidence,
            hyps,
            self.pack.graph,
            state,
            engine,
            result,
        )
        ranked = sorted(result["posterior_map"], key=result["posterior_map"].get, reverse=True)
        has_transfer = select_transfer_problem(self.pack.items, scenario.target_concept) is not None

        if scenario.expects_abstention:
            correct = outcome.decision == "abstain"
        else:
            correct = result["top_hypothesis"] == scenario.true_gap_label

        # §7.5 calibration logging (logging only — never acted on yet):
        # predict the top gap's probability, observe whether the learner's
        # underlying evidence was actually correct.
        observed = 1.0 if scenario.current_evidence.evaluation.get("correct") else 0.0
        self.calibration_log.append(
            {
                "scenario_id": scenario.id,
                "subject": scenario.subject,
                "predicted_confidence": round(result["top_posterior"], 3),
                "observed_correct": observed,
                "expects_abstention": bool(scenario.expects_abstention),
            }
        )

        return {
            "scenario_id": scenario.id,
            "subject": scenario.subject,
            "name": scenario.name,
            "true_gap_label": scenario.true_gap_label,
            "expects_abstention": scenario.expects_abstention,
            "decision": outcome.decision,
            "action": outcome.action,
            "initial_top": initial_top.concept_id if initial_top else None,
            "initial_entropy": initial_entropy,
            "turns": result["turns"],
            "final_entropy": result["final_entropy"],
            "final_top": result["top_hypothesis"],
            "top_posterior": result["top_posterior"],
            "insufficient_evidence": result["insufficient_evidence"],
            "top3": ranked[:3],
            "correct": correct,
            "has_transfer_item": has_transfer,
            "diagnostic_question_ids": [t["question_id"] for t in result["transcript"]],
            "entropy_reduction": (
                1 - result["final_entropy"] / max(initial_entropy, 1e-9) if initial_entropy > 0 else 0.0
            ),
        }

    def calibration_summary(self, records) -> dict:
        if not records:
            return {"logged_records": 0, "bins": []}
        edges = [0.4, 0.5, 0.6, 0.7, 0.8, 1.0001]
        labels = [f"[{a:.1f}, {b:.1f})" for a, b in zip(edges[:-1], edges[1:])]
        bins = {label: [] for label in labels}
        for rec in records:
            p = float(rec["predicted_confidence"])
            idx = next(i for i, edge in enumerate(edges[1:]) if p < edge)
            bins[labels[idx]].append(rec)
        bin_rows = []
        for label, recs in bins.items():
            if not recs:
                continue
            mean_pred = sum(r["predicted_confidence"] for r in recs) / len(recs)
            obs = sum(r["observed_correct"] for r in recs) / len(recs)
            bin_rows.append(
                {
                    "confidence_range": label,
                    "records": len(recs),
                    "mean_predicted": round(mean_pred, 3),
                    "observed_correct_rate": round(obs, 3),
                }
            )
        return {"logged_records": len(records), "bins": bin_rows}

    def evaluate(self, subject: str, active: bool = True) -> dict:
        start = len(self.calibration_log)
        scenarios = build_scenarios(subject, self.pack)
        runs = [self.run_scenario(s, active=active) for s in scenarios]
        gap_runs = [r for r in runs if not r["expects_abstention"]]
        abstain_runs = [r for r in runs if r["expects_abstention"]]

        gap_correct = sum(1 for r in gap_runs if r["correct"]) if gap_runs else 0
        abstain_correct = sum(1 for r in abstain_runs if r["correct"]) if abstain_runs else 0
        top1 = gap_correct / len(gap_runs) if gap_runs else 0.0
        abstain_acc = abstain_correct / len(abstain_runs) if abstain_runs else 0.0
        top3 = (
            sum(1 for r in gap_runs if r["true_gap_label"] in r["top3"]) / len(gap_runs)
            if gap_runs
            else 0.0
        )
        turns = sum(r["turns"] for r in runs) / len(runs) if runs else 0.0
        entropy_red = sum(r["entropy_reduction"] for r in runs if r["initial_entropy"] > 0) / max(
            sum(1 for r in runs if r["initial_entropy"] > 0), 1
        )
        transfer_coverage = sum(1 for r in runs if r["has_transfer_item"]) / len(runs) if runs else 0.0

        return {
            "subject": subject,
            "scenario_count": len(runs),
            "gap_scenarios": len(gap_runs),
            "abstention_scenarios": len(abstain_runs),
            "top1_gap_accuracy": round(top1, 3),
            "top3_gap_recall": round(top3, 3),
            "abstention_accuracy": round(abstain_acc, 3),
            "avg_diagnostic_turns": round(turns, 2),
            "avg_entropy_reduction": round(entropy_red, 3),
            "transfer_item_coverage": round(transfer_coverage, 3),
            "calibration": self.calibration_summary(self.calibration_log[start:]),
            "calibration_records": self.calibration_log[start:],
            "runs": runs,
        }

    def evaluate_all(self, active: bool = True, subjects=("DSA", "Biology")) -> dict:
        reports = {}
        for subject in subjects:
            reports[subject] = self.evaluate(subject, active=active)
        return reports


def evaluate_all_subjects(active: bool = True, subjects=("DSA", "Biology"), pack_for=None) -> dict:
    """Evaluate every subject with its own domain pack (scenarios are pack-specific)."""
    pack_for = pack_for or (lambda s: get_pack(s))
    reports = {}
    for subject in subjects:
        reports[subject] = EvaluationHarness(pack_for(subject)).evaluate(subject, active=active)
    return reports


def compare_active_vs_passive(subject: str, pack) -> dict:
    harness = EvaluationHarness(pack)
    return {
        "passive": harness.evaluate(subject, active=False),
        "active": harness.evaluate(subject, active=True),
    }


def main() -> None:
    from adaptive.domains import get_pack

    all_reports = evaluate_all_subjects()
    artifact_lines = []
    artifact_lines.append(
        {
            "type": "meta",
            "schema": "AURA calibration log \u00a77.5",
            "note": "predicted (top gap posterior) vs observed (learner evidence correct). Logging only - never acted on.",
            "generated": "2026-08-18",
        }
    )

    for subject, report in all_reports.items():
        compare = compare_active_vs_passive(subject, get_pack(subject))
        print(f"== {subject} ==")
        print(f"  gap scenarios:        {report['gap_scenarios']}   abstention scenarios: {report['abstention_scenarios']}")
        print(f"  top-1 gap accuracy:   {report['top1_gap_accuracy']}   (active diagnostics)")
        print(f"  top-3 gap recall:     {report['top3_gap_recall']}")
        print(f"  abstention accuracy:  {report['abstention_accuracy']}")
        print(f"  avg diagnostic turns: {report['avg_diagnostic_turns']}")
        print(f"  avg entropy reduction:{report['avg_entropy_reduction']}")
        print(f"  transfer coverage:    {report['transfer_item_coverage']}")
        passive_acc = compare["passive"]["top1_gap_accuracy"]
        active_acc = compare["active"]["top1_gap_accuracy"]
        print(f"  active-vs-passive top-1: {passive_acc} -> {active_acc}")
        for r in report["runs"]:
            tag = "ABSTAIN" if r["expects_abstention"] else ("OK " if r["correct"] else "MISS")
            if r["expects_abstention"]:
                info = f"decision={r['decision']}"
            else:
                info = f"true={r['true_gap_label']:<26} top={r['final_top']:<26} turns={r['turns']}"
            print(f"    [{tag}] {r['scenario_id']:>6} {info}")

        cal = report["calibration"]
        print(f"  calibration log: {cal['logged_records']} (predicted, observed) pairs - logging only, not acted on")
        for b in cal["bins"]:
            print(f"    {b['confidence_range']:<12} n={b['records']:<4} mean_pred={b['mean_predicted']:<6} observed_correct_rate={b['observed_correct_rate']}")
        for rec in report["calibration_records"]:
            artifact_lines.append(rec)

    try:
        import json
        from pathlib import Path

        out = Path("artifacts") / "calibration_log.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as fh:
            for line in artifact_lines:
                fh.write(json.dumps(line) + "\n")
        print(f"\n  calibration artifact -> {out}")
    except OSError as exc:  # pragma: no cover - read-only cwd etc.
        print(f"\n  (could not write calibration artifact: {exc})")


if __name__ == "__main__":
    main()