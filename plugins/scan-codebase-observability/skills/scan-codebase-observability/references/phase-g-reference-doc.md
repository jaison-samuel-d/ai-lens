# Phase G — Generate the reference document

The point of this phase: someone opens this file six months from now, having forgotten most of this conversation, and needs to find "where do I see the faithfulness score" or "is this evaluator actually trustworthy" without re-deriving it from the code. Write for that reader.

## Where it goes

A single file in the target repo, e.g. `LANGFUSE_OBSERVABILITY_REFERENCE.md`, committed as part of the same PR as everything else. Use `assets/reference-doc-template.md` as the structure.

**Before finalizing the path, confirm it is not covered by an existing `.gitignore` rule** (e.g. `git check-ignore <path>` returns nothing for it). A reference document that lives in an ignored location is invisible to everyone else and defeats the entire purpose of writing it down — this has happened before: a prior version of exactly this kind of document was written into a gitignored `docs/` folder and was later lost completely, with only a changelog entry left behind describing rich content (rubric text, setup notes) that no longer existed anywhere. Prefer the target repo's root, or another location already known to be tracked.

## Required content

1. **A short "where things live" section** at the top: which Langfuse dashboard(s) exist and their names, which Dataset holds the calibration set (and its current size — say if it's still small/growing), which Experiments are wired into CI if any, and a plain-language summary of the masking rules applied.
2. **The metric table** — one row per metric (native and custom), with: metric name, native or custom, how it's computed (which evaluator, which prompt file/version if applicable), the Langfuse score name, exactly where to find it in the Langfuse UI (which dashboard, which widget, which filter — not just "in Langfuse somewhere"), which stated goal it maps to, and its calibration status (calibrated against N dataset examples / provisional with N annotated cases).
3. **What Langfuse does *not* cover** — restate the infra-metrics scope note plainly here too; this is the single most likely point of future confusion for someone who wasn't in this conversation.

## Regeneration discipline

This document gets regenerated on future drift re-scans (Phase H). **Diff against the existing file and merge, don't blind-overwrite** — if a human has hand-edited it (added a note, corrected something), a silent overwrite destroys that. Where content conflicts, prefer accuracy (a metric that no longer exists shouldn't linger) but preserve human-authored prose additions where they don't directly contradict the regenerated facts.
