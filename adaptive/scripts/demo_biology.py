from __future__ import annotations

"""AURA 60-second proof-of-generality demo - Biology / theory evidence adapter.

Same core loop, same LearningGap object, different evidence adapter (OCR'd MCQ
+ spoken answer instead of executable code).

Run:  python -m adaptive.scripts.demo_biology
"""

import json

from adaptive.privacy.capsule import PRIVACY_CLAIM
from adaptive.core.graph_projection import render_learning_map
from adaptive.core.session import AdaptiveSession
from adaptive.domains import get_pack


def _posterior_bars(snapshot) -> str:
    ranked = snapshot.ranked()[:4]
    width = 24
    lines = []
    for h in ranked:
        filled = int(h.posterior * width)
        lines.append(f"    {h.concept_id:<28} {'#' * filled:<{width}} {h.posterior:.2f}")
    return "\n".join(lines)


def seed_history(session: AdaptiveSession) -> None:
    session.start_session("BIO-20260813-S02")
    for i, (day, hour) in enumerate(((11, 12), (13, 12))):
        session.observe(
            {
                "session_id": session.current_session_id,
                "timestamp": f"2026-08-{day:02d}T{hour:02d}:00:00+05:30",
                "concept": "golgi",
                "secondary_concepts": ["rough_er"],
                "question_id": f"q{i}",
                "selected_option": 1,
                "correct_option": 0,
                "distractor_pattern": "attributed_packaging_to_rer",
                "recurrence": True,
                "input_mode": "voice",
            }
        )


def main() -> None:
    pack = get_pack("Biology")
    session = AdaptiveSession(pack)
    seed_history(session)

    print("=" * 76)
    print("AURA - same engine, different evidence adapter")
    print("Biology: OCR + voice -> diagnosis -> contrastive explanation -> discriminative check")
    print("=" * 76)

    print("\n[1] LEARNER SCANS A PRINTED CELL-BIOLOGY QUESTION\n")
    print("    Camera -> crop -> on-device OCR -> extracted text preview -> user confirms")
    print('    extracted: "Which organelle is primarily responsible for modifying, sorting,\n'
          '                and packaging proteins for secretion?"')

    print("\n[2] LEARNER ANSWERS BY VOICE (STT -> structured evidence)\n")
    print('    spoken answer: "the rough ER"')
    session.observe(
        {
            "timestamp": "2026-08-17T13:00:00+05:30",
            "concept": "golgi",
            "secondary_concepts": ["rough_er"],
            "question_id": "scan_42",
            "selected_option": 1,
            "correct_option": 0,
            "distractor_pattern": "attributed_packaging_to_rer",
            "recurrence": True,
            "input_mode": "voice",
        }
    )
    print("    VERDICT: WRONG (packaging is a Golgi job)   |   distractor pattern: attributed_packaging_to_rer")
    print("    historical recurrence: yes (2 prior sessions)")
    st = session.state.state("golgi")
    print(f"    BKT belief for golgi after evidence: {st.mastery_belief:.2f} ({st.current_status})")

    print("\n[3] AURA DOES NOT JUST MARK IT WRONG - it checks the hypothesis distribution\n")
    snap = session.diagnose()
    print("    blocking-gap hypotheses:\n")
    print(_posterior_bars(snap))
    print(f"    entropy H = {snap.entropy:.2f}")

    print("\n[4] ONE DISCRIMINATIVE DIAGNOSTIC (information-gain maximising)\n")
    q = session.engine.select_question(snap.hyps, pack.questions("diagnostic"))
    print(f"    {q.prompt}")
    for i, opt in enumerate(q.options):
        print(f"      {chr(65 + i)}) {opt}")
    signature = max(range(len(q.options)), key=lambda i: q.likelihood["mc_rer_golgi_confusion"][i])
    print(f"\n    LEARNER ANSWERS: {chr(65 + signature)}) {q.options[signature]}")

    print("\n[5] POSTERIOR COLLAPSES TOWARD THE RER/GOLGI CONFUSION\n")
    snap2 = session.answer_diagnostic(q, signature)
    print(_posterior_bars(snap2))

    print("\n[6] TRUSTED CONTRASTIVE EXPLANATION (retrieval-grounded, cited)\n")
    outcome = session.decide(snap2)
    bundle = session.retrieve("golgi", "golgi modifies sorts packages proteins", k=2)
    response = session.teach(outcome, "golgi", bundle)
    print(f"    AURA ({response.action}):")
    print(f"      {response.message}")
    if response.citations:
        print(f"    grounded in: {response.citations}")
    if response.next_check:
        print(f"    next check:  {response.next_check}")

    print("\n[7] DISCRIMINATIVE FOLLOW-UP - the learner answers correctly\n")
    follow = pack.questions("diagnostic")[0]
    session.observe(
        {
            "timestamp": "2026-08-17T13:01:30+05:30",
            "concept": "golgi",
            "secondary_concepts": ["rough_er"],
            "question_id": follow.id,
            "selected_option": 0,
            "correct_option": 0,
            "distractor_pattern": None,
            "recurrence": False,
            "intervention_id": session.last_intervention_id,
            "input_mode": "voice",
        }
    )
    st2 = session.state.state("golgi")
    print(f"    BKT belief for golgi: {st2.mastery_belief:.2f} ({st2.current_status})")

    print("\n[8] LEARNING MAP - RER vs Golgi state has moved\n")
    print(render_learning_map(pack.graph, session.state, "Biology"))

    print("\n[9] PRIVACY INSPECTOR - what WOULD be sent, nothing was\n")
    capsule = session.privacy_capsule(bundle=bundle)
    print("    \"" + PRIVACY_CLAIM + "\"")
    print("\n    capsule (dry_run=true - no remote call exists in this engine):")
    for line in json.dumps(capsule, indent=2).splitlines():
        print("      " + line)
    print("\n    Remote (if ever gated) = only this capsule; voice text, history, and state stay local.")

    print("\n    Same core: OBSERVE -> STATE -> DIAGNOSE -> ASK -> TEACH -> VERIFY -> UPDATE")


if __name__ == "__main__":
    main()