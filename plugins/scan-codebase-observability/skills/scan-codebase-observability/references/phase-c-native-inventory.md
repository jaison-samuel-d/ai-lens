# Phase C — Inventory what Langfuse already gives you

Do this before building anything custom in Phase D. Building a bespoke version of something Langfuse already does natively wastes effort and creates a second source of truth that will drift.

## Native, free from tracing alone (once Phase B is done)

- Latency, token usage, and cost — per trace, per session, per user.

## Native, but needs to be configured/used, not built

- **LLM-as-a-judge evaluators** — judge-model scoring on production traces, configurable via UI or API, running at the individual-operation level (not just whole traces), supporting categorical as well as numeric verdicts.
- **Human annotation queues** — manual review/labeling workflow, supports sessions as well as traces/observations.
- **Custom code evaluators** and a **Scores API/SDK** — the mechanism Phase E uses to push anything this skill computes itself.
- **Datasets + Experiments** — offline test sets, prompt/model/code comparison, regression gating. This is the store Phase D3 reads from and writes into.
- **Score analytics and custom dashboards** — a widget/Metrics-API system for trending any trace/observation/score dimension.
- **Native User Feedback scores** — explicit thumbs-up/down and similar, useful raw material for Phase D3's reference-free tier.

## Not native — this is the real gap Phase D fills

- Infrastructure metrics (CPU, memory, non-LLM request latency, queue depth) — not ingested by Langfuse at all. If the stated goal needs these, they belong on a separate OTel/Prometheus/Grafana path, not inside Langfuse. Say this plainly to the user rather than letting them assume Langfuse covers it.
- Any domain-specific quality metric — faithfulness, hallucination rate, tool-call correctness, task completion, and everything else in the Phase D taxonomy. None of this is pre-built.
- Score-threshold alerting — not clearly documented as a native feature as of this writing. Verify directly against current Langfuse docs before telling a user it exists; if it doesn't, Phase H's fallback is polling the Metrics API and routing to whatever alerting system the org already uses.

## What to produce from this phase

A short list, in plain language, of "here's what you get for free once tracing is on" to include in the final reference document (Phase G) — this is often the most immediately useful thing to tell a user who assumed they'd have to build cost/latency tracking themselves.
