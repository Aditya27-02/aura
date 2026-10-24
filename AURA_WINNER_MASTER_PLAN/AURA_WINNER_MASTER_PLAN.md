# AURA — Winner Master Plan
## Active Gap Diagnosis Engine for Adaptive Learning
**Status:** Supersedes `FINAL_ADAPTIVE_LEARNING_SYSTEM_PLAN_V2_FINAL.md` and the gap-audit review. Single source of truth.
**Problem alignment:** PS17 (Learning Gap Detection) primary, PS10 (Personalized Learning Companion) as the closed-loop remediation layer.

---
## 1. Core Thesis

> **Most systems know a student got something wrong. AURA determines, with quantified uncertainty, *why* — asks the one question that resolves the ambiguity, teaches only the confirmed gap, and verifies real understanding on a transfer problem before it believes the gap is closed.**

One sentence for judges, investors, and users alike:

> **"AURA doesn't just detect that you're wrong. It actively decides what evidence it needs before deciding what to teach — and it proves you actually learned before it moves on."**

Everything in this document exists to make that loop (a) real, (b) measurable, (c) hard to copy, and (d) buildable in hackathon time.

```
OBSERVE → LEARNER STATE → DIAGNOSE (uncertainty) → ASK / TEACH → VERIFY (transfer) → UPDATE STATE
```

This is the entire product. Voice, OCR, QLoRA, curriculum graphs, and agents are subsystems in service of this loop — none of them is the pitch.

---

## 2. What This Is Not (Unchanged From Source, Reaffirmed)

Not a chatbot. Not a RAG tutor. Not a multi-agent swarm. Not an education super-app. Not a GraphRAG demo. Not a marks dashboard. Not a system that permanently labels the learner. Not a cloud database owning long-term learner memory.

2026 prior art (DeepTutor, LearnerCoMPASS, GraphMASAL, RAG-KT, LongTutor) already ships RAG + memory + agents + adaptive questions + learning dashboards. None of that is novelty. This plan explicitly does not compete on feature-checklist parity — it competes on **one mechanism executed to a depth nobody else demonstrates, with proof.**

---

## 3. The Moat (5+ Year Defensibility)

A competitor can add an LLM, a RAG pipeline, agents, or GraphRAG to their tutor in a sprint. None of that reproduces what compounds here. The moat is **not an algorithm** (information gain is public math) — it is **four data/evaluation assets that only accumulate through real usage and cannot be bootstrapped from a general-purpose model**:

| Moat layer | What it is | Why it compounds | Why an LLM/RAG bolt-on can't copy it |
|---|---|---|---|
| **1. Diagnostic-question effectiveness table** | Per (concept, misconception-class, question-template) → measured information gain achieved *in practice*, not theoretical | Every real diagnostic session refines which questions actually discriminate hypotheses vs. which merely sound diagnostic | Requires thousands of real (question → posterior shift) pairs; a competitor starts at zero and needs the same volume of real learner interactions to catch up |
| **2. Intervention → recovery → transfer outcome table** | Per (gap type, intervention type, learner-state band) → measured recovery rate and transfer success | This is a causal-adjacent dataset no public tutor publishes; it lets AURA's policy stop guessing which intervention works and start knowing | Generic LLMs have no feedback signal for "did this explanation actually produce durable, transferable understanding" — that signal only exists inside a system that runs verification-with-transfer as a first-class step (Gap 5/6 fix, §7) |
| **3. Longitudinal learner-state transition data (de-identified, opt-in aggregate)** | Statistics on how mastery belief, recurrence, and gap status evolve over real multi-week/multi-year usage | Calibration (Gap 14) and cold-start priors (Gap 13) get better with scale; a new entrant's priors stay generic forever | Requires retention over months, which requires the product to already be trusted with privacy-sensitive local memory — a chicken-and-egg advantage once achieved |
| **4. Domain-independent evidence-adapter framework + evaluation harness** | The `EvidenceAdapter → LearnerState → GapHypothesis → Diagnostic → Intervention → Transfer` contract, proven across ≥2 structurally different domains (executable code vs. theory/MCQ) | Each new domain pack (Chemistry, Physics, language learning) is cheap to add once the core loop and evaluation harness exist; a single-domain competitor re-derives this from scratch each time | The harness itself (gold scenarios, adversarial benchmark, ablation infrastructure — §9) is IP that takes real engineering months to replicate credibly, not a weekend feature add |

**The actual defensibility claim, stated precisely (no overclaiming):**
Today, at hackathon scale, there is no moat yet — moats are earned through usage, not architecture diagrams. What this section defines is *which data AURA must start capturing from day one* so that by month 6–12 of real usage, a competitor cannot close the gap by adding components; they would need to independently accumulate the same interaction volume. This is a **hypothesis**, and §12 defines exactly how to validate it (does diagnostic effectiveness actually improve measurably with more logged sessions — track this, don't assume it).

---

## 4. Product Wedge

**Initial wedge (do not widen it prematurely):** competitive-programming / DSA learners who get a wrong-answer verdict and no explanation of *why their mental model is broken* — the single highest-frequency, highest-frustration, most machine-verifiable failure mode in technical education. Judge-testable, quantifiable, executable evidence — no domain in the plan gives cleaner proof.

**Wedge sequencing (do not skip steps):**
1. DSA diagnostic loop only, standalone, no companion polish — prove diagnosis accuracy beats baselines.
2. Add verification-with-transfer (not just "tests pass") — prove recovery is real, not trial-and-error.
3. Add Biology as the *second, structurally different* evidence adapter — prove the loop is domain-independent, not a DSA-specific hack.
4. Only then: multimodal UX, QLoRA, live tutor — these are retention/UX layers, not core-loop proof.

This sequencing is both the hackathon build order (§10) and the startup go-to-market order: ship the wedge, prove it beats baselines, expand adapters, expand modality.

---

## 5. Architecture (Simplified, Unchanged Where the Source Was Already Right)

```
LEARNER
  ↓
INPUT (text / voice / OCR / code)
  ↓
EVIDENCE ADAPTER (domain-specific, normalizes to EvidenceEvent)
  ↓
NAVIGATOR AGENT (routes: diagnose / teach / verify / escalate)
  ↓
LEARNER-STATE ENGINE (deterministic, BKT baseline)
  ↓
GAP HYPOTHESIS ENGINE (Bayesian posterior over candidate gaps)
  ↓
SUFFICIENT EVIDENCE? ──No──→ DIAGNOSTIC QUESTION SELECTOR (max info gain − burden) ──→ back to LEARNER
  │Yes
  ↓
CONSTRAINED RETRIEVAL (subject → concept → metadata → semantic → bounded context)
  ↓
TUTOR AGENT (local SLM + pedagogical QLoRA) ──Verification needed?──→ SUPERVISOR (gated, high-capability)
  ↓
INTERVENTION (hint / explain / worked example / socratic / prerequisite rewind)
  ↓
TRANSFER VERIFICATION (structurally different problem, same concept) ← NEW, see §7
  ↓
MEMORY CURATOR AGENT (only writer; deterministic commit)
  ↓
LEARNER STATE UPDATED + VISIBLE LEARNING MAP UPDATED
```

**Three agents. Two model backends. One deterministic state engine.** No new agent, subsystem, or model is added unless it measurably improves diagnosis accuracy, diagnostic efficiency, recovery rate, transfer rate, personalization, grounding, latency, cost, or privacy (source's own admission rule — kept, and now has actual metrics attached in §9 to enforce it instead of being an assertion).

**Three data objects, unchanged:** Curriculum Graph (static, domain structure) · Learner-State Overlay (per-learner belief state) · Event Ledger (append-only evidence). No calendar graph, no daily/weekly/monthly pipeline — session summaries + threshold compaction only.

**Two model backends, unchanged:** Model A = local quantized SLM (1.7B baseline, 3–4B upper candidate after VRAM benchmark) + one shared pedagogical QLoRA adapter. Model B = gated high-capability supervisor for ambiguity, verification conflicts, and planning — never receives full learner history, only a bounded local context capsule (§8).

---

## 6. LearningGap — First-Class Primitive (Fixes Gap 3)

The single most important schema change from the source plan: promote "gap" from an implicit overlay field into an explicit, queryable, auditable object. This is also the primary unit the moat tables in §3 are built from.

```json
{
  "gap_id": "uuid",
  "concept_id": "binary_search_boundary",
  "misconception_class": "boundary_update_error",
  "hypothesis_probability": 0.81,
  "evidence_ids": ["evt_101", "evt_104", "evt_119", "evt_120", "evt_133"],
  "evidence_count": 5,
  "recurrence_count": 3,
  "prerequisites_affected": ["binary_search", "loop_invariant"],
  "first_detected": "2026-07-02T10:14:00+05:30",
  "last_confirmed": "2026-08-17T22:10:00+05:30",
  "status": "active_blocker",
  "intervention_ids": ["int_44"],
  "reassessment_result": null,
  "transfer_verified": false,
  "recovery_confidence": 0.72
}
```

`status` enum: `candidate → active_blocker → intervention_applied → recovered_pending_transfer → recovered → stale_reassess`. A gap is never `recovered` until `transfer_verified = true` — this single rule closes Gap 5.

Every diagnostic-question and intervention log entry references a `gap_id`, which is exactly what makes the §3 moat tables computable instead of aspirational.

---

## 7. Diagnosis Algorithm + Transfer-Verified Recovery (Fixes Gaps 1, 2, 5, 6, 11, 14)

### 7.1 Hypothesis inference (unchanged core math, reframed language — fixes Gap 2)

```
π_t(g) = P(g | E_1:t, G_K) ∝ P(E | g) P(g)
```

Never say "root cause." Always say **"blocking-gap hypothesis, probability X, based on N evidence items."** This is a diagnostic belief used to decide the next question — not a causal claim. State this explicitly in every UI surface and every judge-facing explanation (fixes Gap 2 directly; also the correct response to "how do you know the inferred misconception is real?").

### 7.2 Active diagnosis (unchanged, this is the strongest asset in the source — keep exactly as specified)

```
H(π_t) = -Σ_g π_t(g) log π_t(g)
IG(q)   = H(π_t) - Σ_y P(y|q) H(π_t+1^(q,y))
q*      = argmax_q [ IG(q) - λ·C(q) ]
```

"Ask the smallest question expected to tell us the most about what's actually wrong." This *is* the killer algorithm identity (fixes Gap 4 — give it a name in every artifact: **the Active Diagnosis Engine**, not "the system").

### 7.3 Abstention state (fixes Gap 11)

When no hypothesis clears a confidence threshold after available diagnostics are exhausted, AURA must have an explicit state — **not** a forced guess:

```
Hypothesis A  0.38
Hypothesis B  0.34
Hypothesis C  0.28
→ INSUFFICIENT EVIDENCE
→ do not teach a specific misconception
→ request one more diagnostic OR escalate to supervisor OR flag "needs more evidence" to learner
```

This is a visible, honest product state, not a failure to hide. It is also what keeps the "we never claim causal root-cause" promise credible under adversarial judge questioning.

### 7.4 Transfer-verified recovery loop (fixes Gap 5 and Gap 6 — the single highest-leverage addition to the whole plan)

The source plan verifies via "tests pass" (DSA) or "answers correctly" (Biology). This is insufficient — passing corrected code can be trial-and-error, not understanding. Add one mandatory stage after every intervention:

```
Problem 1 (original failure)
      ↓ diagnosis
Intervention
      ↓ learner retries Problem 1 → passes
Problem 2 (STRUCTURALLY DIFFERENT, SAME CONCEPT)
      ↓
Did the learner transfer the concept, not just fix one bug?
      ↓
transfer_verified = true/false → gap.status = recovered / recovered_pending_transfer
```

Concretely for DSA: after a boundary-update fix on one binary-search variant, present a different binary-search implementation (e.g., first/last-occurrence variant) rather than a retest of the same code. For Biology: after an RER/Golgi contrastive explanation, ask a discriminative question about a *different* organelle pair or a novel scenario, not a restatement of the same MCQ.

**Headline metric this unlocks (fixes Gap 6):**

```
Learning Gain      = post-intervention competency − pre-intervention competency
Transfer Gain      = performance on structurally novel problem, same concept
Recovery ≠ Passing = recovery requires transfer_verified = true
```

This is the metric that separates AURA from "AI tutor that explains things" — and it is the direct answer to the hardest judge question in the room: *"How do you know the student actually learned, not just copied a fix?"*

### 7.5 Calibration (fixes Gap 14)

Track predicted-confidence vs. actual-correctness for every `hypothesis_probability` and every `mastery_belief`. Log (predicted, observed) pairs into the evaluation harness from day one, even before there's enough data to act on it. Do not display raw probabilities to learners (`"74.238% mastery"` is exactly what the source correctly rejects) — display calibrated status bands (`Verified / Developing / Needs Review / Active Blocker / Stale`) only after the underlying probability has been checked against outcomes, not asserted.

### 7.6 Cold start (fixes Gap 13)

New learner, zero history:

```
Cold-Start Diagnostic Session (5–10 items)
      ↓
prior knowledge + confidence + response pattern + diagnostic answers
      ↓
Initial Learner State (wide uncertainty, informative priors from curriculum position)
      ↓
Active Diagnosis takes over immediately — same engine, not a separate "onboarding quiz" system
```

Cold start is not a special mode; it is the same active-diagnosis loop starting from a maximally uncertain prior. Don't build a second system for this.

---

## 8. Privacy Architecture (Unchanged Substance, Tightened Claim — Fixes Gap 10)

```
DEVICE (private)                          REMOTE (only when gated)
─────────────────                         ─────────────────────────
Event Ledger                              Minimal Context Capsule:
Learner-State Overlay          ──────→      subject, target concept,
Compact History Summaries                   current hypothesis distribution,
Raw diagnostic/intervention log             2–5 relevant evidence items,
                                             bounded retrieved chunks
```

Example capsule (unchanged from source, this was already correct):

```json
{
  "subject": "Biology",
  "target": "RER_vs_Golgi",
  "current_state": {"RER": "developing", "Golgi": "needs_review"},
  "relevant_history": ["confused packaging function twice", "correctly identified ribosomes on RER"],
  "current_evidence": "spoken answer transcript",
  "retrieved_sources": ["chunk-118", "chunk-121"]
}
```

**Exact claim to make, verbatim, everywhere (this is the only privacy sentence to ever say publicly):**
> "Persistent personalization memory stays local; remote services receive only the minimum temporary context required for the current operation."

**Never claim** "all data stays on device" — the code sandbox and gated supervisor are remote by design. This distinction must survive every pitch deck, README, and judge Q&A without drifting toward the stronger, false claim.

Demo requirement (fixes Gap 10's "show the boundary, don't just assert it"): the Progress+Privacy surface must have a literal "what was just sent" inspector showing the actual capsule JSON for the last remote call, so the privacy claim is falsifiable by the judge, not asserted.

---

## 9. Evaluation Infrastructure (Fixes Gaps 1, 4, 12 — This Is Also Moat Layer 4)

### 9.1 Baselines (unchanged, already correctly specified)

| Baseline | Composition |
|---|---|
| A — Generic LLM | user → LLM |
| B — RAG Tutor | user → RAG → LLM |
| C — Memory Tutor | user + recent history → RAG → LLM |
| D — State-Aware Tutor | BKT state + RAG → LLM |
| **AURA (final)** | state + active diagnosis + local adapted SLM + longitudinal memory + gated supervisor + transfer verification |

### 9.2 Core metrics (source list retained, transfer/calibration additions marked NEW)

- **Diagnosis:** Top-1 blocking-gap accuracy, Top-3 recall, false-gap rate, diagnostic turns required, confidence calibration (NEW: logged from day 1 per §7.5).
- **Active diagnosis:** entropy reduction per diagnostic, questions-to-disambiguate, unnecessary-diagnostic rate.
- **Recovery / Transfer (NEW, fixes Gap 6):** recovery rate, transfer rate, Recovery-vs-Passing gap (fraction of "passed" cases that failed transfer — this number, if nonzero, is itself proof the transfer step matters).
- **Personalization:** recurrence detection rate, prerequisite relevance, unnecessary repetition, stale-memory error rate.
- **Teaching:** targeted pre/post improvement, answer-leakage rate, hint dependence.
- **RAG:** evidence coverage, citation correctness, unsupported-claim rate.
- **Systems:** local SLM latency p50/p95, supervisor escalation rate, cost/tokens, peak VRAM, retrieval latency.

### 9.3 Adversarial / ambiguous-learner benchmark (NEW, fixes Gap 12)

Real learners produce evidence that isn't clean signal. Build gold scenarios covering:

```
correct answer for wrong reason        correct code, misunderstood concept
wrong answer from a careless mistake   wrong code from syntax, not concept
correct answer by guessing             conflicting evidence across sessions
repeated misconception                 correct answer, poor explanation
```

A system that only proves itself on clean gold scenarios hasn't proven anything a skeptical judge or a real deployment will accept. This benchmark is also a direct contributor to moat layer 1 (§3) — every adversarial case that gets a wrong diagnosis becomes a labeled training example for the diagnostic-effectiveness table.

### 9.4 Ablation table (unchanged, already correct — this is the falsification discipline that keeps scope honest)

| Variant | State | Active Diagnosis | RAG | QLoRA | Long-term Memory | Supervisor | Transfer Verification |
|---|---:|---:|---:|---:|---:|---:|---:|
| Generic LLM | No | No | No | No | No | No | No |
| RAG | No | No | Yes | No | No | No | No |
| Stateful RAG | Yes | No | Yes | No | Yes | No | No |
| Active Diagnostic | Yes | Yes | Yes | No | Yes | No | No |
| Adapted Local | Yes | Yes | Yes | Yes | Yes | No | No |
| **AURA (final)** | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | **Gated** | **Yes** |

Kill rule, unchanged: a component survives only if it measurably improves a metric in §9.2 relative to the row above it. QLoRA specifically: benchmark Base → Prompted → RAG → QLoRA → QLoRA+state → full system; delete QLoRA from the demo entirely if it doesn't clear the bar (source's own instruction — this plan does not relax it).

---

## 10. MVP Scope — Build Now / Later / Reject

### Build now (hackathon-critical, Tier 1)

1. LearningGap object + Learner-State Overlay + Event Ledger (local schema, §6).
2. BKT baseline + Bayesian gap hypotheses + information-gain diagnostic selector (§7.1–7.3).
3. DSA evidence adapter: sandbox execution, hidden tests, structured evidence, one curriculum subgraph (binary search + boundary/loop-invariant misconceptions is enough).
4. **Transfer verification stage** for DSA (§7.4) — this is the single highest-ROI new build in this entire plan.
5. Gold evaluation scenarios + baselines A–D + core metrics harness (§9.1–9.2) — build this *before* polishing UI, per the source's own Phase 0 instinct, which this plan strengthens into a hard gate: no fine-tuning or demo polish work starts until the harness can score at least the DSA gap set.
6. Minimal UI: Study Workspace (code mode) + Gap Panel + Learning Map, enough to run the demo flow.

### Build if time remains (Tier 2)

7. Biology evidence adapter (second, structurally different domain — proves generality, not a second feature).
8. Local SLM (1.7B) + pedagogical prompting, no QLoRA yet.
9. Cold-start diagnostic session (§7.6).
10. Calibration logging pipeline (§7.5) — logging only, not acting on it yet.
11. Privacy capsule inspector UI (§8).

### Build only after Tier 1–2 are measured (Tier 3)

12. QLoRA adapter — only with an A/B result showing improvement; otherwise skip entirely for the demo.
13. Gated supervisor escalation.
14. Adversarial/ambiguous-learner benchmark expansion (§9.3).

### Explicitly reject for MVP (unchanged kill list from source, still correct)

Agent swarm · one LLM per subject · one LoRA per user or per subject before evidence · cloud learner graph · attendance/timetable/certificates/social feed · generic LMS · emotion detection · full diagram understanding · unsupervised RL policy without longitudinal data · heavy graph database on Android · raw multi-year context in prompts · voice/OCR/live-tutor UX before the core loop is proven (source correctly listed these as Phase 8; this plan makes explicit that they must never be built before Tier 1 is measured, not just built later in sequence).

**Rule for all three tiers:** nothing in Tier 2 or 3 is admitted unless it improves a metric from §9.2 — this is not a feature roadmap, it's a gated experiment list.

---

## 11. Killer Demo (Fixes Gap 16)

Single flagship demo. Do not split attention across DSA + Biology + voice + OCR with equal weight (fixes Gap 7's "breadth trap").

**4-minute main demo — DSA diagnostic + transfer loop:**

1. Learner submits binary-search code. Normal cases pass; two boundary cases fail.
2. AURA does not explain immediately. It shows: *"I see two plausible reasons for this failure"* — hypothesis distribution rendered live (boundary-update 0.46 / termination-logic 0.39 / comparison-logic 0.15).
3. AURA asks the one diagnostic question maximizing information gain: *"If `mid == low`, what guarantees the interval shrinks?"*
4. Learner answers. Posterior updates live on screen: boundary-update 0.84 ↑, others collapse.
5. AURA gives a hint — not the fixed code. Learner corrects the implementation. Original tests pass.
6. **AURA does not mark this recovered.** It presents a structurally different binary-search variant (first-occurrence search). Learner solves it.
7. Only now: gap status flips `active_blocker → recovered`, Learning Map updates, transfer_verified = true is shown explicitly on screen.

**60-second proof-of-generality demo — Biology:** same engine, same LearningGap object, same diagnosis math, different evidence adapter (OCR'd MCQ + spoken answer instead of code execution). This is framed explicitly as *"same core, different evidence adapter"* — visually reuse the same architecture diagram from the DSA demo with the DSA-specific box swapped, so judges see one engine, not two projects.

Everything else (voice, live tutor, QLoRA) is mentioned as roadmap, never demoed live unless Tier 1–2 is fully working with time to spare.

---

## 12. Startup / YC Strategy

**Painful problem:** learners (and after-the-fact, tutoring companies / edtech platforms) currently get pass/fail signal with generic remediation; nobody productizes "why," verified. This is validated by the 2026 competitive landscape itself (§2) — every major player added memory/RAG/agents and still ships guess-then-explain, not diagnose-then-verify.

**Wedge → expansion path (mirrors §4, restated as GTM):**
1. DSA/competitive-programming learners (individual, high-frequency pain, machine-verifiable proof).
2. Coding bootcamps / CS departments (B2B2C — instructors want diagnostic-quality data on *why* students are stuck, which nobody currently has).
3. Second-domain adapters (Biology → any exam-prep subject with MCQ/short-answer evidence) once the domain-pack interface is proven.
4. Licensing the evaluation harness + diagnostic-effectiveness dataset itself (moat layer 1 and 4, §3) to other edtech tooling as an assessment-quality API — this is the highest-margin long-term expansion and the most defensible, since it requires the accumulated interaction data this plan is architected to capture from day one.

**Compounding data advantage (the actual YC-grade answer to "why can't a bigger company just build this"):** a well-funded competitor can copy the architecture in this document in a month. They cannot copy the diagnostic-effectiveness table, the intervention-outcome table, or the calibration curves without running the same volume of real, transfer-verified learner interactions — and until they have that data, their diagnosis is guessing exactly like Baseline B/C in §9.1. This is a data-flywheel moat, not a technology moat, and it is only real if §3's tables are actually populated starting from the first user session — a build requirement, not an aspiration.

**Distribution:** competitive-programming communities and CS course integrations are natural low-CAC channels because the wedge (§4) is already where the target user's pain is highest and most quantifiable — a "your diagnosis was right / wrong" feedback button doubles as both product and free labeled data for moat layer 1.

**What must NOT be claimed to investors or judges without the evidence existing (unchanged from source, reaffirmed as non-negotiable, §14):** no accuracy numbers, no user counts, no revenue, no "better than ChatGPT," no patents, until measured.

---

## 13. Defensibility Stress-Test (Fixes Gap 18, Section F of the brief)

| Attack | Why it fails against AURA specifically |
|---|---|
| "We'll just add information-gain question selection to our chatbot." | The math is public (§7.2), but without a `LearningGap` primitive (§6), transfer verification (§7.4), and a calibration/effectiveness log (§3), that's a feature, not a system — it produces guesses with no way to know if the guesses are improving. |
| "We'll add a knowledge graph and memory like DeepTutor/LearnerCoMPASS." | Already commoditized per §2's own research audit — this is explicitly not the claimed differentiator. |
| "We'll fine-tune a bigger model." | Doesn't address diagnosis; a bigger model still can't distinguish "passed the test" from "understood the concept" without the transfer-verification step (§7.4), which is a product/data design choice, not a model-capability problem. |
| "This is just BKT + active learning, textbook ML." | Correct, and stated openly (§7.1–7.2) — the moat was never claimed to be the math. It's the compounding effectiveness/outcome data (§3) that only a real deployed loop generates. |
| "Judges will say the demo is scripted." | Live posterior updates on-screen (§11 step 2/4) and the explicit `transfer_verified` state change are falsifiable in real time — not narrated, shown. |

**Honest residual risk:** if usage volume never reaches the scale needed to populate §3's tables meaningfully, the moat does not materialize and this becomes "well-designed tutor with good UX," not a defensible company. This is stated as a risk, not hedged away — see §14.

---

## 14. Risks and What We Will Not Claim

| Risk | Mitigation | Owner |
|---|---|---|
| Data flywheel never reaches scale to matter | Instrument moat tables from session 1; track table-size vs. diagnostic-accuracy correlation explicitly as a KPI, don't assume it | Product |
| Transfer verification adds friction, hurts UX/retention | A/B test friction vs. trust; may need to make transfer check lightweight (1 item) not heavy | Product |
| Calibration takes too long to become trustworthy | Log immediately, act on calibrated bands only after N≥threshold observations; show uncalibrated status as "Developing (early data)" until then | Eng |
| 8GB VRAM constraint kills QLoRA plan | Benchmark 1.7B first; only attempt 3–4B after measured headroom (source's own rule, kept) | Eng |
| Judges conflate "passed tests" with "understood concept" | Make transfer_verified a visible on-screen state change in the demo (§11) so the distinction is impossible to miss | Product |
| Scope creep back toward the original fragmented 4-agent/9-screen design | §10's tier gating is a hard build order, not a suggestion — nothing in Tier 2/3 starts before Tier 1 is measured | Eng lead |

**Never claim without evidence (unchanged from source, still binding):** human-level tutoring, causal root-cause detection, guaranteed learning, zero hallucination, "all data stays on device" when the supervisor/sandbox is remote, works for every subject, better than ChatGPT without a benchmark, real forgetting prediction without longitudinal calibration, an RL-optimized policy without training data. Add to this list: **no diagnostic-accuracy or moat claims until §9's harness produces the numbers** — this plan defines how to get them, not what they will be.

---

## 15. Execution Priorities (Ordered, Final)

1. LearningGap primitive + local schema (§6, §10 Tier 1.1).
2. Diagnosis engine: BKT + Bayesian hypotheses + information-gain selector + abstention state (§7.1–7.3).
3. Gold evaluation harness + baselines A–D (§9.1–9.2) — **gate everything after this on the harness existing.**
4. DSA evidence adapter + sandbox (§10 Tier 1.3).
5. Transfer verification stage (§7.4) — highest single-item ROI in this plan.
6. Minimal demo UI: gap panel with live posterior, transfer step visible (§11).
7. Biology adapter as proof of generality (§10 Tier 2.7).
8. Everything else (local SLM, QLoRA, calibration display, supervisor, voice/OCR/live tutor) — only after 1–7 are measured and working, in the order listed in §10.

**Final freeze statement:** the architecture is intentionally smaller than the original nine-subsystem plan. It is:

```
Learner State + Active Diagnosis + Transfer-Verified Recovery + Trusted Retrieval + Local Specialized Tutor + Longitudinal Local Memory
```

Three agents coordinate those functions. The graph represents curriculum structure and the learner's evolving relationship to it. The mathematics is used only where it has a defensible probabilistic or information-theoretic interpretation. The large model is used only where the small model is insufficient. No component is added — to the demo, the codebase, or the pitch — unless it moves a number in §9.2.
