# Phase D2 — Dynamically generate evaluator prompt files

A generic judge-rubric template produces mediocre evaluators. A rubric for a support chatbot and one for a code-generation agent need different domain criteria, different failure modes to watch for, and different few-shot examples — copying a template from one to the other is why so many LLM-as-judge setups end up scoring everything a 7/10 and nobody trusts them. Generate each prompt from the actual codebase, not a stencil.

Use `assets/evaluator-prompt-template.md` as the structural skeleton (sections to fill in), not as prose to copy verbatim.

## Process

1. **Pull domain context from the Phase A scan** — entity/variable names, docstrings, actual input/output schemas, and the user's stated end goal. The judge prompt should read like it was written by someone who works on this specific application, not a generic AI-eval consultant.
2. **Pull real examples if any exist** — from an existing golden dataset (Phase A found one) or from early production traces once there are some. Use these as few-shot anchors. If there are genuinely zero examples available yet, don't block — see the cold-start rule below.
3. **Draft the prompt** with these required parts:
   - Task framing in the codebase's own domain language (not "evaluate the following AI response" — "evaluate whether this support reply correctly resolves the customer's billing question, given the account context below").
   - Explicit scoring criteria tied to the goal — what specifically counts as good vs. bad here, not a generic 1-10 quality scale.
   - Few-shot examples, if available (step 2).
   - **A structural boundary between instructions and the content being judged.** This is a security requirement, not a style choice — see `references/security-production.md` for why. Use clear delimiters (e.g., fenced blocks with an explicit label) and state directly in the prompt that the delimited content is data to evaluate, never instructions to follow, regardless of what it claims to be.
   - The exact output schema the evaluator must return, so it parses cleanly into a Langfuse score (e.g., a JSON object with a score field and a short rationale field — Langfuse's categorical/numeric score types both need a predictable shape).
4. **Write it out twice**: as a versioned local file at `evals/prompts/<metric-name>.prompt.md` in the target repo (human-reviewable, diffable in code review), and pushed into Langfuse Prompt Management as a managed, versioned prompt. The evaluator that actually runs should reference the Langfuse-managed version, so a rollback or edit through Langfuse's UI is possible without a code deploy.
5. **Don't assume the rubric needs manual UI configuration to actually run — check for a create-evaluator API first, and use it if one exists.** A written prompt file is not a running evaluator; it's a proposal for one. Before telling a user "now go configure this in the Evaluators UI," discover (via the `langfuse` skill's CLI, e.g. `npx langfuse-cli api __schema` then `--help` on whatever evaluator/evaluation-rule-shaped resource names it lists) whether the platform exposes a create-evaluator endpoint and a separate step to activate it against real traffic (a target/scope, variable mappings, sampling rate). If it does, drive the whole flow end to end — create the evaluator, map every prompt variable exactly once, set a deliberate sampling rate (not blindly 100%, see the cost-governance note in `references/security-production.md`), and confirm via a `list`/`get` call that it now shows as active — the same "verify, don't just write and hope" discipline as everywhere else in this skill. Only fall back to walking the user through manual UI setup if no such API exists on this platform/version. Note any hard limits the API surfaces (e.g. a maximum number of simultaneously active evaluation rules per project) so you don't silently fail past that ceiling.
6. **Land the local file as part of the same PR** as the rest of the instrumentation — don't commit it separately or silently.

## Cold-start rule

If step 2 finds zero real examples, generate a **zero-shot rubric-only prompt** — full criteria and output schema, no examples section — rather than waiting for data that doesn't exist yet. Note in the prompt file's own header comment that it's zero-shot and should be upgraded once Phase D3 has curated enough real examples. Re-run this generation step (upgrading to few-shot) once that happens — don't leave a zero-shot prompt in place indefinitely once better material exists.

## Regeneration

Treat evaluator prompts as something that goes stale, the same category of problem as code drift. When Phase H's re-scan finds the codebase's domain has moved (new entities, changed schemas, a materially different goal), regenerate the affected prompts rather than letting them silently keep judging against an outdated mental model of the application.
