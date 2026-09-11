# scan-codebase-observability

A Cowork/Claude Code plugin that wraps the `scan-codebase-observability` skill: instrument a codebase for LLM/agent observability with [Langfuse](https://langfuse.com), and build goal-driven custom evals — even when no labeled/golden dataset exists yet.

## What it does

When invoked against a target codebase (attached to the session or a connected folder), the skill:

1. **Detects** the existing stack, entry points, and any prior Langfuse/OTel instrumentation, ad hoc eval scripts, committed secrets, or existing golden datasets (via `scripts/scan_codebase.py`).
2. **Instruments** the app with the Langfuse SDK if it isn't already set up, wiring PII/secret masking before any trace data ships, plus session/user/environment tags.
3. **Inventories** what Langfuse already gives natively (cost, tokens, latency, LLM-as-judge evals, datasets, dashboards) before building anything custom.
4. **Selects custom metrics** driven by the user's stated end goal for the application (RAG quality, agent/tool-use correctness, safety, business KPIs, cost efficiency) rather than a fixed checklist.
5. **Generates evaluator/judge prompts** dynamically from the codebase's own domain language, hardened against prompt injection.
6. **Builds evals without a golden dataset**, via a tiered reference-free strategy that bootstraps a dataset from production over time.
7. **Pushes scores** to Langfuse via the Scores API and surfaces them on a custom dashboard.
8. **Validates** the setup before calling it done.
9. **Generates a reference document** mapping every metric to where to find it in Langfuse.
10. **Documents lifecycle** guidance: online evaluators, drift re-scans, dataset growth, CI gating.

All code, prompt, or CI-gate changes land as a branch/PR for human review — the skill never commits directly to a protected branch or wires up auto-merge, and it never touches credential/secret files directly.

## When it triggers

Use it whenever you ask Claude to add observability, monitoring, tracing, evals, LLM-as-a-judge, or Langfuse to a codebase or LLM/agent app; ask what metrics or evals an AI app should track; ask how to evaluate an LLM app without a labeled dataset; or want a production-ready observability/eval setup for an AI product — even without saying "Langfuse" explicitly.

## Structure

Lives at `plugins/scan-codebase-observability/` within the `ai-lens` marketplace repo:

```
scan-codebase-observability/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── scan-codebase-observability/
│       ├── SKILL.md
│       ├── references/       # one file per phase (A–H), read on demand
│       ├── assets/           # evaluator prompt & reference-doc templates
│       └── scripts/
│           └── scan_codebase.py
└── README.md
```

## Requirements

- A target codebase attached to the session, or a connected folder — the skill will ask for one rather than fabricating findings.
- The user's stated end goal for the application (what "working well" means), which steers which custom metrics get built.
- A Langfuse account/project (the skill installs and configures the SDK; it does not create the Langfuse account for you).

## Installing

This plugin is published from the `ai-lens` marketplace (see the repo root
README). From Claude Code:

```
/plugin marketplace add jaison-samuel-d/ai-lens
/plugin install scan-codebase-observability@ai-lens
```

To develop against a local checkout instead, load it directly from disk via
the Agent SDK's `plugins` option (see `d:\insight-pipeline\backend\app\runner.py`
for a working example) — no install step needed for that path.
