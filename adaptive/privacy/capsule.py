"""§8 Privacy Architecture.

Persistent personalization memory stays local; remote services receive only the
minimum temporary context required for the current operation. This module builds
that minimal context capsule so the boundary is *shown*, not asserted: the demo
inspectors render the exact JSON that would accompany any remote call.
"""

from __future__ import annotations

from typing import Optional

from adaptive.core.session import AdaptiveSession

PRIVACY_CLAIM = (
    "Persistent personalization memory stays local; remote services receive only "
    "the minimum temporary context required for the current operation."
)


def build_capsule(
    *,
    subject: str,
    target: str,
    current_state: dict,
    relevant_history: list[str],
    current_evidence: str,
    retrieved_sources: list[str] | None = None,
    dry_run: bool = True,
) -> dict:
    """Build the §8 minimal-context capsule in its exact JSON shape.

    ``dry_run=True`` records that *nothing was actually transmitted*: this phase
    of the engine has no remote call at all, so the capsule is always shown in
    the privacy inspector as "what would be sent", keeping the claim falsifiable.
    """
    capsule = {
        "subject": subject,
        "target": target,
        "current_state": dict(current_state),
        "relevant_history": [str(h) for h in relevant_history][:5],
        "current_evidence": str(current_evidence),
        "retrieved_sources": [str(s) for s in (retrieved_sources or [])][:5],
        "dry_run": bool(dry_run),
    }
    return capsule


def _history_summaries(events, k: int = 3) -> list[str]:
    summaries: list[str] = []
    for ev in reversed(events[:k]):
        result = ev.evaluation.get("correct") if isinstance(ev.evaluation, dict) else None
        parts = [f"{ev.activity or 'attempt'} on {'+'.join(ev.concepts or [])}"]
        if result is True:
            parts.append("correct")
        elif result is False:
            failed = ev.evidence.get("failure_classes") if isinstance(ev.evidence, dict) else None
            if failed:
                parts.append("failed " + ", ".join(failed))
            else:
                parts.append("incorrect")
        if isinstance(ev.evidence, dict) and ev.evidence.get("recurrence"):
            parts.append("recurring")
        summaries.append(" — ".join(parts))
    return summaries


def build_session_capsule(session: AdaptiveSession, *, retrieved_sources=None) -> dict:
    """Derive the capsule from live session state (the privacy inspector)."""
    target = session.active_event.concepts[0] if session.active_event else None
    neighbors = session.pack.graph.concept_neighborhood(target, depth=1) if target else []

    current_state = {}
    for cid in ([target] + sorted(neighbors)) if target else []:
        st = session.state.state(cid)
        current_state[cid] = st.current_status

    bundle_sources = [] if retrieved_sources is None else list(retrieved_sources)
    if not bundle_sources and getattr(session, "last_bundle", None) is not None:
        bundle_sources = list(session.last_bundle.citations)

    current_evidence = ""
    if session.active_event is not None:
        failed = session.active_event.evidence.get("failure_classes") if isinstance(session.active_event.evidence, dict) else None
        if failed:
            current_evidence = f"{session.active_event.activity or 'submission'} failed: {', '.join(failed)}"
        else:
            current_evidence = f"{session.active_event.activity or 'submission'} (all checks passed)"

    return build_capsule(
        subject=session.pack.subject,
        target=target or "none_yet",
        current_state=current_state,
        relevant_history=_history_summaries(session.ledger),
        current_evidence=current_evidence,
        retrieved_sources=bundle_sources,
        dry_run=True,
    )