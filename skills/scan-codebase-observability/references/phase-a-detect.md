# Phase A — Detect

Goal: understand what's actually in the codebase before changing anything. Everything downstream depends on getting this right, so don't skip straight to instrumenting because you recognize the framework.

## Run the scanner first

Run `scripts/scan_codebase.py <path-to-target-repo>` and read its JSON output before doing anything by hand. It deterministically checks for:

- Language/framework fingerprint (manifest files: `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json`, `Cargo.toml`)
- Existing Langfuse markers (`langfuse` in manifests, `@observe`, `Langfuse(`, `langfuse.openai`, `LANGFUSE_*` env var references)
- Existing OpenTelemetry markers (`opentelemetry`, `TracerProvider`, OTel exporter config)
- Ad hoc eval-looking code (files/functions with names like `eval`, `score`, `judge`, `ragas`, `ground_truth`)
- Anything that looks like an existing golden/labeled dataset (`datasets/`, `evals/fixtures/`, `golden/`, or similarly named directories with structured examples)
- A lightweight secret scan (regex patterns for API-key-shaped strings, cloud credential patterns, common secret env var names) — this flags file:line only, never the value itself

Trust the scanner for the mechanical part; use your own judgment on top of it for things a regex can't catch — e.g., whether an "agent orchestration loop" pattern is present, or which entry points are actually load-bearing versus dead code.

## Things to work out beyond the scan

- **Architecture pattern**: monolith, microservices, serverless/functions, batch/data pipeline, or LLM/agent application (often more than one applies). This shapes what "entry point" even means for this codebase.
- **Real entry points**: HTTP routes, queue/event consumers, cron jobs, CLI commands, and — the ones that matter most here — LLM call sites, tool/function-call sites, retrieval/vector-store calls, agent orchestration loops.
- **Deployment target for Langfuse**: Cloud vs. self-hosted. Infer a lean from what's already in the repo (existing self-hosted infra suggests self-hosted; nothing suggests cloud is the lower-friction default) but don't decide silently — if the stated goal implies compliance or data-residency sensitivity, or if the scanner found anything that looks like regulated data, surface the decision to the user explicitly rather than picking for them. See `references/security-production.md` for what's actually available (regions, HIPAA readiness, self-host isolation).
- **Any manual eval process already running** (a notebook, a cron script computing quality scores by hand) — plan to migrate this into Langfuse's evaluator/score system in Phase D rather than leaving a parallel, undocumented system running alongside the new one.
- **Where logging actually surfaces.** Check whether the codebase's logger writes to console/stdout, a file, or another structured sink (e.g. a Python `logging.basicConfig(filename=...)` call, a JS logger configured with a file transport). Phase F's validation leans heavily on reading application logs to confirm instrumentation actually fired — if logs are file-routed, note the path now. Otherwise a later validation step can wrongly conclude "this didn't work" just because an expected line never appeared in the terminal, when it was written to a file the whole time.
- **Whether more than one tracing/observability SDK is already active** — Langfuse alongside LangWatch, Datadog, New Relic, a generic OpenTelemetry setup, Langsmith, or similar, from a prior integration effort that was layered on rather than replaced. Flag this explicitly and see the dedicated section below — sharing one OTel provider (covered next) is necessary but not sufficient once two vendors are both instrumenting the same call sites.
- **Whether the working tree already has a large uncommitted diff** touching the same files this skill would instrument. If so, stop and ask the user how they want to sequence commits — their existing work as its own PR first, bundled together with this skill's changes, or set aside — before adding more on top of it. Don't assume.

## If the scanner finds Langfuse already set up

Don't re-instrument. Move to Phase C to inventory what's already flowing, and treat Phase B as an audit ("is the existing setup missing masking? session tags? a shared OTel provider it should be attached to?") rather than a fresh install. Flag gaps you find rather than silently leaving them.

## If the scanner finds an existing generic OpenTelemetry `TracerProvider`

Note this specifically for Phase B — Langfuse's SDKs (Python v3+/JS v4+) are themselves OTel-based, and the correct move is attaching a `LangfuseSpanProcessor` to the existing provider rather than standing up a second, isolated one. A second isolated provider can orphan spans whose parent/child relationship crosses the provider boundary.

## If more than one tracing/observability SDK is already present

Sharing one OTel `TracerProvider` (above) does not by itself guarantee both vendors' traces come through complete. When two SDKs both instrument the same call sites — e.g. both attached as callbacks on the same LLM/agent-framework invocation, or both auto-instrumenting the same HTTP client — each vendor's exporter commonly applies its own span-export filter that only forwards spans it recognizes as its own or as a "known" instrumentation source. Spans created by the *other* vendor's tracer can be silently dropped from the first vendor's UI, with no error anywhere. The result is a trace tree that looks plausible but is quietly missing spans — worse than an obviously broken setup, because it creates false confidence.

Before treating multi-backend tracing as working:
- Fire one real request and inspect each vendor's own debug-level logs for language like "dropping span," "skipping," or "filtered" (naming varies by SDK).
- If a vendor's SDK exposes a way to customize its export filter (an allow-list of instrumentation scope/source names is common), check whether the other vendor needs to be added to it.
- Don't conclude nothing is missing just because traces "look complete" in one vendor's UI — wrapper/intermediate spans are exactly the ones most likely to get filtered, while leaf-level spans that happen to carry vendor-agnostic semantic-convention attributes are more likely to survive by accident, giving a misleadingly reassuring partial picture.

## Output of this phase

A short internal summary (doesn't need to be shown to the user yet) covering: stack, architecture pattern, entry points, Langfuse/OTel status (including any second observability SDK found), where logs actually surface, secrets found (flagged, not printed), existing dataset status, working-tree state, and the cloud/self-host lean. Carry this into Phase B.
