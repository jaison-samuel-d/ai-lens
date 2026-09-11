# Phase D3 — Evals without a golden dataset

This is the phase most likely to get skipped or half-done, because the instinct when someone says "we don't have labeled data" is to say "then let's build some first." Don't. Most useful eval signal doesn't need ground truth, and a labeled set is something a working eval system grows into, not a precondition for having one at all. **If Phase A found no existing dataset, that changes which tier you start at — it does not mean you wait.**

## The tiered strategy

Run these in order; each tier catches what the previous one can't, and together they cover a working eval system with zero labeled data as a starting point.

### Tier 1 — Code evaluators on every trace
Deterministic, zero cost, zero labels: schema validity, required-field presence, "was the expected tool called," step-budget respected, valid JSON output. These run on 100% of traffic because they're cheap and need no judge-model call at all. Build these first, always, regardless of whether a dataset exists — they're the foundation even when it does.

**Never let a Tier 1 check fail silently.** A code evaluator that pushes a score should log distinctly for every outcome — success, an exception, AND any precondition that causes it to skip (e.g. no active trace/span in the current context, a missing required field, the scoring client not yet initialized). A guard written as `if precondition: push_score()` with no `else`/log branch makes a real, recurring failure indistinguishable from "this metric simply had nothing to report yet" — this is a real, hard-to-diagnose failure mode that has actually occurred, not a hypothetical one. When Phase F validates a Tier 1 evaluator, deliberately exercise the "precondition not met" path once (not just the happy path) and confirm it logs something, so a silent no-op can never masquerade as calm, uneventful success.

### Tier 2 — LLM-as-judge with rubric-only prompts, on a sampled subset
No reference answer needed. The judge scores against explicit criteria from the Phase D2 prompt — is the answer grounded in the retrieved context or tool output, does it address the stated goal, is it safe, is it on-tone — rather than comparing to a gold answer. This is the mechanism behind most of the Phase D taxonomy already being reference-free. Sample rather than running on every trace; see the cost-governance note in `references/security-production.md` for why 100% coverage isn't the goal.

### Tier 3 — Route disagreement and low-confidence cases to a human annotation queue
This substitutes for a pre-built golden set. Send cases where Tier 2's judge output is low-confidence, or where multiple signals disagree (e.g., a user gave a thumbs-down but the judge scored it well), to a Langfuse annotation queue for a human to actually look at. This is real calibration data, generated as a byproduct of running in production rather than as an upfront data-labeling project.

### Tier 4 — Fold in production signals as a free reference-free proxy
Native Langfuse user feedback (explicit thumbs up/down) plus implicit signals worth wiring in even without formal scoring: did the user rephrase the question, retry, abandon the session, or escalate to a human. These are cheap and somewhat noisy, but real, and cost nothing extra to capture if session/user tagging from Phase B is already in place.

### Tier 5 — Curate into a growing dataset
The real disagreements and failures surfaced by Tiers 2–4 get curated into a Langfuse Dataset over time. **This is the same store the "already has a golden dataset" path reads from directly** — the two starting conditions converge on one place. The only difference between "has a dataset" and "cold start" is whether this store begins populated or begins empty and fills in from production.

## Calibration under this path

Calibration means checking judge-vs-human agreement on whatever's been annotated so far (Tier 3's output), not a one-time check against a static set. Recheck periodically as the dataset grows — an evaluator checked against 3 annotated cases is genuinely less trustworthy than one checked against 50, even though both technically "passed calibration" at some point. **Record which state applies and say so explicitly everywhere calibration status appears** (Phase F's validation, Phase G's reference document): "calibrated against N dataset examples" vs. "provisional — N annotated cases so far." Never present a provisional evaluator's output with the same confidence as a fully calibrated one.

## The one rule that matters most in this phase

Never tell a user "you need a labeled dataset before we can set up evals." Say instead: here's what runs today with zero labels (Tiers 1 and 2), here's how disagreement gets routed to a human for calibration (Tier 3), and here's how the dataset builds itself from there (Tier 5). That's the actual answer to "we don't have a golden dataset yet."
