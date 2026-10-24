from __future__ import annotations

from adaptive.types import Event


def normalize_code_event(raw: dict) -> Event:
    """Code evidence adapter: turn test results into a structured learning event.

    raw keys:
      session_id, timestamp, concept, secondary_concepts, code,
      test_results, failure_classes, static_pattern, recurrence,
      complexity, input_mode, evidence_extra
    """
    failure_classes = list(raw.get("failure_classes") or [])
    passed = list(raw.get("test_results", {}).get("passed") or [])
    failed = list(raw.get("test_results", {}).get("failed") or [])
    correct = not failed

    evidence: dict = {}
    if raw.get("static_pattern"):
        evidence["pattern"] = raw["static_pattern"]
        evidence["implementation_evidence"] = raw["static_pattern"]
    if raw.get("recurrence"):
        evidence["recurrence"] = True
    if failure_classes:
        evidence["failure_classes"] = failure_classes
    evidence["concept_strengths"] = raw.get("concept_strengths", [1.0, 0.35, 0.2])
    evidence.update(raw.get("evidence_extra") or {})

    return Event(
        event_id=raw.get("event_id", ""),
        session_id=raw.get("session_id", ""),
        timestamp=raw.get("timestamp", ""),
        subject="DSA",
        concepts=[raw["concept"]] + list(raw.get("secondary_concepts") or []),
        activity="code_submission",
        input_mode=raw.get("input_mode", "code"),
        response={"code": raw.get("code")},
        evaluation={
            "correct": correct,
            "hidden_tests_passed": len(passed),
            "hidden_tests_failed": len(failed),
            "failure_classes": failure_classes,
            "complexity_intent": raw.get("complexity"),
        },
        evidence=evidence,
        intervention_id=raw.get("intervention_id"),
        outcome="passed" if correct else "failed",
    )