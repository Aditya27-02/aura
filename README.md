# AURA — Adaptive Learning Diagnosis Engine (PS17 / PS10)

AURA is a local-first Python core engine for diagnosing **blocking gaps**, not just
announcing wrong answers. It follows the strict requirements in
[`AURA_WINNER_MASTER_PLAN`](AURA_WINNER_MASTER_PLAN/AURA_WINNER_MASTER_PLAN.md):

- `LearningGap` is a **first-class primitive** with a status lifecycle.
- The system **abstains** when evidence is insufficient — it never forces a guess.
- A gap is **not `recovered` until it passes a structurally different transfer
  problem** (`transfer_verified = true`).
- Diagnosis is **active** — it asks the one question that maximises information gain.
- Outcomes are scored against an **adversarial gold benchmark**.
- Learner memory is committed through a **deterministic one-writer** store.

## Why not “mark wrong and move on”?

A single failing answer maps to many possible causes (a missing prerequisite, a
stuck loop bound, an off-by-one slip, an implementation bug). AURA keeps an
explicit hypothesis distribution over these and reduces uncertainty before
teaching, grounding every explanation in retrieved, cited content.

## Quick start

The package is **not installed**; run from the repo root with `PYTHONPATH` set.

```powershell
$env:PYTHONPATH = (Get-Location).Path

# Killer demo: DSA diagnostic + transfer-verified recovery loop
python -m adaptive.scripts.demo_dsa

# Same engine, different evidence adapter (Biology OCR/voice)
python -m adaptive.scripts.demo_biology

# Gold-benchmark evaluation (top-1, top-3, abstention, turns)
python -m adaptive.evaluation.harness

# Engine and API tests
python -m pytest -q tests server/tests
```

Once installed via `pip install -e .`, the same entry points are available as
`adaptive-demo-dsa`, `adaptive-demo-bio` and `adaptive-eval`.

## Web demo

From the repository root, install backend dependencies with
`python -m pip install -r server/requirements.txt`. Use Node.js 24 LTS, then run
`npm ci --prefix frontend` and `npm run build --prefix frontend`. Start the local
demo with `python -m uvicorn server.main:app --host 127.0.0.1 --port 8000`
and open http://localhost:8000.

See [publication validation](PUBLICATION_VALIDATION.md) for version selection,
checks and limitations. The research plans include future work; the current demo
uses simulated evidence.

## Architecture at a glance

```
observe ──► LearnerStateEngine (BKT) ──► DiagnosisEngine (Bayesian gaps)
   │               │                            │  IG question selection
   │               ▼                            ▼
   │         GapRegistry (LearningGap lifecycle) ◄── active diagnosis
   │               │
   ▼               ▼
RetrievalEngine ─► Tutor (contrastive/hint, grounded, cited) ─► transfer-verified verify
   │
   └──► MemoryCurator ──► MemoryStore (deterministic one-writer commit)
   │
   └──► PrivacyCapsule: "what would be sent" (dry_run), never more than §8 minimal context
```

The harness additionally logs **§7.5 calibration pairs** (predicted top-gap
probability vs. observed learner correctness) to `artifacts/calibration_log.jsonl`
from day one — logging only, never acted on. Cold start (§7.6) is the same
active-diagnosis loop starting from maximally uncertain priors; there is no
second onboarding system.

See [`docs/architecture.md`](docs/architecture.md) for detail.

## Kill rule

A new component may only be added if it measurably improves **diagnosis, teaching,
verification, personalisation, grounding, latency, cost, or privacy**. The engine
also never claims a causal root cause: it reports a *blocking-gap hypothesis with
probability X based on N evidence items*.

## Domains

- **DSA** (`adaptive/domains/dsa`): binary search, boundaries, loop invariants;
  code-submission evidence (test failures + static patterns).
- **Biology** (`adaptive/domains/biology`): cell organelles; MCQ / OCR / voice
  evidence with distractor patterns.

## Privacy (showing the boundary, not asserting it)

Section 8 of the plan defines the exact claim:

> "Persistent personalization memory stays local; remote services receive only
> the minimum temporary context required for the current operation."

`adaptive/privacy/capsule.py` builds that minimal capsule (subject, target,
status bands — never raw probabilities — bounded history, current evidence,
retrieved sources) with `dry_run=true`; both demos end with a literal
"[PRIVACY] what would be sent" inspector so the claim is falsifiable by a judge.

## Layout

```
adaptive/
  types.py                  dataclasses (LearningGap, TransferCheck, …)
  core/
    curriculum_graph.py     static concept graph (prereq/part/related/confused)
    learner_state.py        BKT beliefs + status bands
    diagnosis.py            Bayesian gap hypotheses, IG selection, abstention
    gaps.py                 LearningGap lifecycle + transfer helpers
    retrieval.py            grounded content retrieval with citations
    teaching.py             policy (decide_outcome) + deterministic Tutor
    memory.py               one-writer proposal curator
    session.py              granular closed-loop product API
    graph_projection.py     visible learner map (gap-oriented)
  storage/sqlite_store.py   deterministic one-writer commit
  evaluation/               adversarial gold scenarios + harness
  domains/{dsa,biology}/    domain packs (curriculum, evidence, items, corpus)
  scripts/                  killer demos
```
