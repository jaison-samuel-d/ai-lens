<!--
Template for the Phase G deliverable: LANGFUSE_OBSERVABILITY_REFERENCE.md
Fill in every [BRACKETED] section. This file is regenerated on drift re-scans —
diff against the existing version and merge rather than overwrite blindly;
see references/phase-g-reference-doc.md for the regeneration discipline.
-->

# Langfuse Observability Reference — [application name]

Last generated: [date] · Owner: [name/team] · Review cadence: [e.g. "revisit on major drift re-scan, or quarterly"]

## Scope

This document covers LLM/agent-layer observability and evaluation via Langfuse. It does **not** cover infrastructure metrics (CPU, memory, non-LLM request latency) — those live at: [path/link to the separate OTel/Prometheus/Grafana setup, or "not yet set up" if none exists].

Deployment: [Langfuse Cloud (region: [US/EU/Japan/HIPAA]) | Self-hosted]. Chosen because: [one sentence — data residency, compliance, existing infra, etc.].

## Where things live

- **Dashboards**: [dashboard name(s) and what each shows]
- **Dataset (golden/calibration set)**: [Dataset name] — currently [N] curated examples. [Started pre-populated | Started empty and is growing from production feedback.]
- **CI/CD Experiments**: [Experiment name(s) wired into CI, or "not yet gated — dataset still building toward a size where this makes sense"]
- **Masking rules applied**: [one-paragraph plain-language summary of what gets redacted before reaching Langfuse]

## Metrics

| Metric | Native or custom | Computed by | Langfuse score name | Where to find it in Langfuse | Maps to goal | Evaluator/prompt version | Calibration status |
|---|---|---|---|---|---|---|---|
| [e.g. cost per trace] | Native | — (automatic from tracing) | — | Traces view, per-trace cost column | [goal] | — | — |
| [e.g. faithfulness] | Custom | LLM-as-judge, `evals/prompts/faithfulness.prompt.md` v[N] | `faithfulness_score` | [Dashboard] → widget "[widget name]"; also: Traces → filter by score name `faithfulness_score` | [goal this maps to] | Langfuse-managed prompt `[name]`, v[N] | [Calibrated against dataset (N examples) | Provisional — N annotated cases so far] |

<!-- Add one row per metric actually implemented. Delete example rows before shipping. -->

## What's intentionally not built

[List anything from the Phase D taxonomy that was considered and deliberately skipped, and why — e.g. "answer-correctness-vs-reference: no reference answers exist for this use case, so this metric isn't implemented; faithfulness and task-completion cover the same quality concern without needing one."]
