# Phase H — Lifecycle

What keeps this healthy after the initial setup, so it doesn't quietly rot the way most observability efforts do six months in.

## Lean on Langfuse's own online evaluators for the ongoing production loop

Once Tier 2 evaluators (phase-d3) are running as configured online evaluators in Langfuse itself, most of the continuous-monitoring work is native — you don't need to build a separate scheduler. Configure sampling rate and any always-evaluate triggers (flagged sessions, low user-feedback scores) once, then let it run.

## Keep the dataset growing

Production failures and Tier-3 disagreements (phase-d3) should keep flowing into the Langfuse Dataset, not just during initial setup. If you're revisiting this codebase later, check whether that curation is actually still happening — it's easy for the annotation-queue habit to lapse once the initial push is over.

## Gate CI/CD once the dataset is meaningful

Don't wire a CI-blocking gate against a 3-example dataset — that's more likely to block a good PR on noise than catch a real regression. Once the dataset has enough real, curated examples to be statistically meaningful for the metrics in question, add an Experiment-based gate: run the evaluator suite against the dataset on each PR, block on regression past a threshold the user agrees to. Treat any judge-based gate as a candidate for the ensemble-judging hardening described in `references/security-production.md`, since a CI-blocking score is exactly the kind of high-stakes decision worth not trusting to a single judge call.

## Re-scan on drift

Re-run Phase A's scanner periodically (or when a significant PR touches the instrumented paths) to catch new entry points that lack instrumentation, and to detect when the codebase's domain has moved enough that Phase D2's evaluator prompts should be regenerated. Regenerate the Phase G reference document at the same cadence, using its diff/merge discipline rather than a blind overwrite.

## What "done" looks like

Not a one-time deliverable — an operating system with an owner. Before considering this phase complete, make sure the reference document (Phase G) names who owns it and roughly how often it should be revisited, so it doesn't become the kind of documentation that's accurate on day one and wrong by month three.
