from __future__ import annotations

from adaptive.types import Event


def normalize_mcq_event(raw: dict) -> Event:
    """Theory evidence adapter for a multiple-choice answer.

    raw keys:
      session_id, timestamp, concept, secondary_concepts, question_id,
      selected_option, correct_option, distractor_pattern, recurrence,
      input_mode (voice|text|ocr)
    """
    selected = raw.get("selected_option")
    correct = raw.get("correct_option")
    is_correct = selected == correct
    evidence: dict = {}
    if raw.get("distractor_pattern") and not is_correct:
        evidence["distractor_pattern"] = raw["distractor_pattern"]
    if raw.get("recurrence"):
        evidence["recurrence"] = True
    evidence["concept_strengths"] = raw.get("concept_strengths", [1.0, 0.35])

    return Event(
        event_id=raw.get("event_id", ""),
        session_id=raw.get("session_id", ""),
        timestamp=raw.get("timestamp", ""),
        subject="Biology",
        concepts=[raw["concept"]] + list(raw.get("secondary_concepts") or []),
        activity="answered_mcq",
        input_mode=raw.get("input_mode", "text"),
        response={"question_id": raw.get("question_id"), "selected_option": selected},
        evaluation={
            "correct": is_correct,
            "selected_option": selected,
            "correct_option": correct,
            "question_id": raw.get("question_id"),
        },
        evidence=evidence,
        outcome="passed" if is_correct else "failed",
    )


def normalize_answer_event(raw: dict) -> Event:
    """Theory evidence adapter for short answer / spoken explanation.

    raw keys:
      session_id, timestamp, concept, secondary_concepts, answer,
      explanation_eval (pattern string), correct, recurrence, input_mode
    """
    is_correct = bool(raw.get("correct"))
    evidence: dict = {}
    if not is_correct and raw.get("explanation_eval"):
        evidence["distractor_pattern"] = raw["explanation_eval"]
    if raw.get("recurrence"):
        evidence["recurrence"] = True
    evidence["concept_strengths"] = raw.get("concept_strengths", [1.0, 0.35])

    return Event(
        event_id=raw.get("event_id", ""),
        session_id=raw.get("session_id", ""),
        timestamp=raw.get("timestamp", ""),
        subject="Biology",
        concepts=[raw["concept"]] + list(raw.get("secondary_concepts") or []),
        activity="short_answer" if raw.get("input_mode") != "voice" else "spoken_explanation",
        input_mode=raw.get("input_mode", "text"),
        response={"answer": raw.get("answer")},
        evaluation={"correct": is_correct, "explanation_eval": raw.get("explanation_eval")},
        evidence=evidence,
        outcome="passed" if is_correct else "failed",
    )


def normalize_ocr_event(raw: dict) -> Event:
    """OCR adapter: a scanned question becomes a normal theory event after user confirmation."""
    inner = dict(raw)
    inner.setdefault("input_mode", "ocr")
    if raw.get("activity") == "short_answer":
        return normalize_answer_event(inner)
    return normalize_mcq_event(inner)