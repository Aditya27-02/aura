# Architecture — AURA core engine

This document describes the Python core implemented in `adaptive/`. It is aligned
with `AURA_WINNER_MASTER_PLAN/AURA_WINNER_MASTER_PLAN.md`.

## Design invariants

1. **Never force a guess.** If the posterior confidence is below the teaching
   threshold or the question set is uninformative, the system returns
   `decision = abstain`. In the harness this is scored against explicit
   `expects_abstention` scenarios.
2. **`LearningGap` is first-class.** A gap is a persisted object, not a log line,
   with `status`, `recurrence_count`, `hypothesis_probability`, evidence ids,
   intervention ids, and `transfer_verified`.
3. **Recovery requires transfer.** `mark_original_recovered` moves a gap to
   `recovered_pending_transfer`; only `verify_transfer` with a passing
   *structurally different* problem moves it to `recovered`.
4. **No causal claims.** AURA reports *“blocking-gap hypothesis with probability X
   based on N evidence items.”*
5. **One writer, deterministic commit.** All learner-memory mutations flow through
   `MemoryCurator.propose*` → `MemoryStore.validate_and_commit`; there is exactly
   one path that mutates persisted state.
6. **Kill rule.** Any new component must measurably improve diagnosis, teaching,
   verification, personalisation, grounding, latency, cost, or privacy.

## Component map

### `core/curriculum_graph.py`
Static concept graph `G_K` with edge kinds `prerequisite`, `part_of`, `related`,
`confused_with`. Each `ConceptNode` can carry misconception ids. The graph drives
hypothesis generation (prerequisites become candidate gaps) and the visible
learning map.

### `core/learner_state.py`
Bayesian Knowledge Tracing per concept:

```
p_obs = P(correct | p)                     # slip/guess applied
p_update = p + strength · (p_obs − p)      # strength scales implication
followed by the standard transit/correct-and-guessed marginals
```

The *primary* concept of an event receives `strength = 1.0`; secondary concepts
receive weaker strengths (default `[1.0, 0.35, 0.2, …]`). Belief is clamped to
`[0, 1]`. Status bands: `verified`, `developing`, `needs_review`,
`active_blocker`. `recurrence_count` comes from the memory event ledger.

### `core/diagnosis.py`
- Generates `GapHypothesis` entries from the event signal (failure classes + static
  pattern + recurrence + concept context) for:
  - misconception ids mapped by curriculum node,
  - prerequisite concepts (weaker prior),
  - the concept itself (implementation bug).
- Computes a normalised posterior distribution over hypotheses.
- **Active diagnosis:** chooses `q* = argmax IG(q) − λ·C(q)` with `λ = 0.25`,
  never re-asks a question already asked in the session, runs at most `max_turns`
  (default 3). If no question clears confidence, returns `insufficient_evidence`.
- **Uninformative learners:** when `informative=False`, answers cannot manufacture
  confidence — this is how the adversarial abstention scenarios are modelled.

### `core/gaps.py`
`GapRegistry` owns the lifecycle:

```
candidate → active_blocker → intervention_applied → recovered_pending_transfer → recovered  (transfer_verified=true)
                                          └────────────→ active_blocker (transfer failed)
any → stale_reassess
```

`select_transfer_problem` picks a *practice/reassessment* item on the same concept
that is distinct from the original problem id. `make_transfer_check` records the
transfer-problem id, prompt, and `structurally_different=True`.

### `core/retrieval.py`
`RetrievalEngine` filters the corpus by subject and concept metadata, ranks by a
lightweight lexical score (query tokens vs. text + titles), and returns an
`EvidenceBundle` with `citations` (source ids). Difficulty can adapt from
learner state. Retrieval backs every teaching message with cited, grounded text.

### `core/teaching.py`
`TeachingPolicy.decide_outcome` maps `(posterior, action)` to
`(abstain | teach, action)`:

- `top_posterior >= 0.70` → `teach` with misconception-specific action
  (`CONTRASTIVE_EXPLANATION` for misconception gaps that recur, `HINT` for
  low-recurrence or implementation-bug gaps, `PREREQUISITE_REWIND` for
  prerequisite gaps, `REASSESS` for candidate gaps).
- otherwise → `abstain` (`action = None`).

The `Tutor` is **deterministic**: hint banks are keyed by gap misconception id
(`adaptive/domains/*/hints.py`), and unused canonical entries sit side-by-side with
retrieved chunks so an LLM backend can be swapped in later without changing the
interface.

### `core/session.py`
`AdaptiveSession` is the granular closed-loop product API used by demos and tests:

```
observe(raw) → update BKT + memory ledger
diagnose()   → DiagnosticSnapshot (hypothesis bars, entropy, IG question)
answer_diagnostic(q, opt) → updated snapshot
decide()     → DiagnosisOutcome (abstain | teach)
retrieve()   → grounded bundle (subject + neighborhood filter)
teach()      → CandidateResponse; materialises + marks the gap intervention applied
verify (via gaps registry) → transfer check
close_session() → one-writer session summary commit
```

### `core/memory.py` + `storage/sqlite_store.py`
`MemoryCurator` ingests events; the `Event` ledger is append-only and each
concept-state update folds in recurrence information. `SessionSummary` records
gaps strengthened/weakened and interventions used. `MemoryStore` commits exactly
one validated `MemoryPatch` at a time (one-writer invariant) and persists
`learning_gaps` including `status` and `transfer_verified`.

### `privacy/capsule.py` (§8)
`build_capsule` / `build_session_capsule` render the exact §8 minimal-context
JSON shape (`subject, target, current_state, relevant_history, current_evidence,
retrieved_sources, dry_run`). `current_state` carries **status bands only**
(Verified / Developing / Needs Review / Active Blocker / Stale) — raw
probabilities are never exported. Every demo ends with a privacy inspector
showing the capsule marked `dry_run=true`, because this engine performs no
remote call: the §8 claim stays falsifiable by construction. `PRIVACY_CLAIM` is
the verbatim §8 sentence.

### Calibration (§7.5)
`EvaluationHarness` logs a `(predicted, observed)` pair per scenario run
(`predicted_confidence` = top-gap posterior, `observed_correct` = whether the
learner's underlying evidence was actually correct). The harness reports binned
confidence tables and the CLI writes `artifacts/calibration_log.jsonl`. This is
**logging only** — no downstream behaviour consumes the data yet.

### Cold start (§7.6)
There is no separate onboarding system. A zero-history learner starts at the
curriculum-position priors (all `needs_review`) and runs the identical
observe → diagnose → ask → teach loop; `tests/test_privacy.py` pins this with
"abstain on one thin careless item" and "converge on recurring evidence".

### `core/graph_projection.py`
Derives the visible learner map from `G_K` + BKT state and renders gap status
`[OK]` / `[~~]` / `[  ]` per node, with prerequisite annotations.

## Evaluation

`evaluation/scenarios.py` defines 6 gold scenarios per subject:

- recurring boundary-update stall (must diagnose `mc_boundary_update`),
- one-off inclusive/exclusive slip (must diagnose `mc_off_by_one`),
- recurring loop-invariant confusion (`mc_loop_invariant_misuse`),
- healthy-history careless slip (**must abstain**),
- correct answer, wrong reason (`explained_invariant_wrong` → diagnose misconception),
- one weak confusing answer on strong history (**must abstain**).

`evaluation/harness.py` scores **top-1 gap accuracy, top-3 recall, abstention
accuracy, diagnostic turns, entropy reduction, and transfer-item coverage**, in
both active (with IG questions) and passive (no questions) modes to prove the
laptop-relevant lift of active diagnosis.

## Reproducing the numbers

```
$env:PYTHONPATH = (Get-Location).Path
python -m adaptive.evaluation.harness
```

Expected (current): DSA `top1 = 1.0`, Biology `top1 = 1.0`, abstention `1.0` both
subjects, active > passive top-1 in both domains.

## Extension path (later phases, out of scope here)

- QLoRA/SLM candidate × question-endorsement ranking replacing the hand-rolled
  `M ⊆ L` mapping,
- on-device OCR/ASR flight with the same adapters (Biology pack already simulates
  OCR/voice evidence),
- Android deployment of the engine (storage already isolated):
  `adaptive/storage/` → room-backed implementation, same one-writer contract.