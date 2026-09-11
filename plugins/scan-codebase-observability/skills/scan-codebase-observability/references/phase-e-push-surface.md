# Phase E — Push scores and surface them in Langfuse

## Push

- Push every custom score (from code evaluators and LLM-as-judge evaluators alike) via Langfuse's Scores API/SDK, attached to the same trace/observation ID the underlying event already has. Don't create a parallel data store — the entire point is that custom and native metrics sit side by side on the same trace.
- Use deterministic score identifiers where the API supports it, so a retried push after a transient failure doesn't create a duplicate rather than overwriting — see the idempotency note in `references/security-production.md`.
- Tag each score with the evaluator/prompt version that produced it (Phase D2's versioned prompt), so a later regression can be traced to a specific evaluator version rather than looking like unexplained noise.

## Surface

**Building a custom Langfuse dashboard is a required deliverable of this phase, not an optional extra done only if the user asks for one.** Every run of this skill that pushes at least one custom score should end with a dashboard combining native metrics (cost, latency, tokens) with the goal-specific custom scores from Phase D — organized around the stated goal, not a generic "everything" dashboard nobody reads. Build it via the API, don't just tell the user to click through the UI themselves.

### How to build it, concretely

1. **Discover the current dashboard/widget API shape live — don't assume field names from memory or a past project.** These endpoints are commonly marked "unstable"/versioned and their exact field names (e.g. an aggregation field called `agg` rather than `aggregation`, or a placement object needing a `type` discriminator) can differ across Langfuse versions. Use the `langfuse` skill's CLI discovery flow (`npx langfuse-cli api __schema`, then `api <resource> --help` for `unstable-dashboards` / `unstable-dashboard-widgets` or whatever the current resource names are) to get the real, current request shape before writing any dashboard-building code — this is the same "verify the installed API surface before calling it" principle as Phase B, applied to a REST API instead of an SDK.
2. **Derive the widget list from what Phase D/E actually produced, not a fixed template.** For every custom score that was actually pushed (Tier 1 code evaluators and any active Tier 2 judges), create one tile showing it (a NUMBER tile for a simple average/rate is a reasonable default), plus a combined trend chart across all of them so regressions are visible over time. Add native-metric tiles (cost, latency) alongside them. This means the dashboard this phase produces will look different for every codebase, matching whatever was actually built for that project's stated goal — never hardcode a specific project's metric names into this step.
3. **Authenticate without ever touching a credentials file.** If the target codebase has its own already-initialized observability client available to run in-process (e.g. importing the app's own client-init function and reusing the live client object it returns), drive the dashboard-building calls through that client's own already-authenticated HTTP session — this means the actual key value is never read, printed, or exported by you at any point, since the target application already loaded it through its own normal config path. Only fall back to asking the user for a key via an environment variable if no such in-process client is reachable (e.g. a static scan with no running app to import from) — never open or paste from a `.env`/secrets file yourself either way.
4. **Record the resulting dashboard/widget IDs and URL** for Phase G's reference document, and re-run this discovery-then-build flow (not a cached copy of last time's request shape) if the target platform's SDK/API version differs from a previous run.
5. If infra/system metrics are also in scope (a separate OTel/Prometheus path, per the scope note in SKILL.md), don't try to force them into the same Langfuse dashboard — Langfuse doesn't ingest them. Link the two views by shared trace IDs or timestamps instead, and say clearly in the reference document (Phase G) that they're two separate systems, not one.

## What this phase hands to Phase F

A list of what was pushed and where it landed (which dashboard, which widgets, which score names) — Phase F validates that this list is actually true, not assumed.
