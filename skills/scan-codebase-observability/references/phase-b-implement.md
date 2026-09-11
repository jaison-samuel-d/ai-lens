# Phase B — Ensure Langfuse is instrumented

Skip the install steps below if Phase A found Langfuse already present — go straight to the audit checklist at the bottom instead.

## SDK vs. Langfuse's own Agent Skill — these do different jobs, use both where available

Langfuse ships an official Agent Skill (`github.com/langfuse/skills`) for coding agents. If it's installed or installable in your environment, use it for the mechanical setup work — it wraps Langfuse's CLI/REST API and knows current best practice for wiring tracing, migrating prompts, and configuring things correctly. **It does not replace installing the Langfuse SDK in the target application** — Langfuse's own documentation says this directly. Runtime tracing requires the SDK embedded in the running app, because that's what actually generates traces as real requests happen. If that Agent Skill isn't available to you, do the SDK wiring directly using the same principles below — the outcome should be equivalent either way.

## Required steps, in order

1. **Install the SDK** for the detected language, pinned to a specific version (not "latest") so a future breaking change doesn't silently alter behavior.
2. **Verify the installed SDK's actual API surface before writing any integration code that calls it — never rely on memorized method names or a generic online example.** SDKs rename, move, or remove methods across major versions (a Python callback handler losing a `get_trace_id()` method in favor of a `last_trace_id` property, a client's top-level `score()` method becoming `create_score()` in a later release — both real examples, not hypothetical), and the version pinned in this repo's lockfile may be older or newer than whatever generic documentation or general training knowledge reflects. Confirm every method name and signature you're about to call against the version actually installed here, before writing the call site:
   - **Python**: `python -c "from pkg import Client; print([m for m in dir(Client) if 'relevant_substring' in m.lower()])"`, or `inspect.signature(Client.method)`.
   - **JS/TS**: check the installed package's own type declarations (`node_modules/<pkg>/dist/**/*.d.ts`), or `node -e "console.log(Object.keys(require('pkg')))"`.
   - **Any language**: check the installed version's own changelog/release notes if there's reason to think it diverges from the latest docs.
   This single check prevents an entire class of bug where code imports cleanly and looks correct, then fails only at runtime — and can fail *completely silently* if the call site's error handling swallows the exception (see Phase D3's note on logging every outcome of a code evaluator, not just the happy path). Re-run this check per SDK, once per target repo — don't assume a version you verified on a previous project still applies here.
4. **Get credentials from the user or existing secret-management convention** — never invent, hardcode, or write keys into a file yourself. If the repo doesn't have an established pattern (a `.env.example`, a secrets-manager reference), ask the user how they want keys supplied rather than choosing for them, and never open or edit any actual `.env`/credentials file.
5. **Configure input/output masking before wiring up any call site.** This is the step most likely to get skipped under time pressure, and it's the one that matters most: Langfuse stores full prompt/completion content by default, unlike some tracing conventions where content capture is opt-in. Write a masking function that redacts PII/secrets patterns relevant to this codebase's domain (not just a generic placeholder — look at what kind of data actually flows through the LLM calls you found in Phase A) and wire it into the client init. Test it against more than one example before moving on (Phase F formalizes this, but don't wait until then to write it).
6. **Instrument the LLM/agent call sites found in Phase A** — native decorators/wrappers, or attach to the existing OTel `TracerProvider` if Phase A found one (see phase-a-detect.md for why this matters).
7. **Attach `session_id`, `user_id`, and an environment tag** (`dev`/`staging`/`prod`) to every trace. Without the environment tag, Phase D3's calibration and Phase H's CI gating can't reliably separate environments later — this is cheap to add now and expensive to retrofit.
8. **Migrate hardcoded prompts into Langfuse Prompt Management**, if any exist. This isn't cosmetic: without it, a later score regression can't be distinguished from a prompt change vs. a model change vs. real drift.
9. **Land all of this as a branch/PR**, never a direct commit — see the non-negotiables in SKILL.md.

## Audit checklist (when Langfuse is already present)

Check for and flag, don't silently fix without telling the user:
- Is masking configured at all? If not, this is a real gap — call it out prominently, not as a minor note.
- Are session/user/environment tags present on traces?
- Is there an isolated second `TracerProvider` that should be merged with an existing one?
- Are prompts still hardcoded despite Langfuse being present (a common half-migration)?

## Known roadblock: `CERTIFICATE_VERIFY_FAILED` reaching Langfuse Cloud on corporate-managed Windows machines

Observed in practice, not hypothetical: after wiring the SDK and adding real API keys, every network call to `cloud.langfuse.com` (prompt push, trace/generation export, score push) can fail with:

```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

**Do not reach for `verify=False` or a disabled-verification `httpx_client=` as the first move.** That masks the symptom and quietly weakens TLS for a tool now carrying real (masked, but still real) production data. Diagnose first — the cause is almost always one of these, roughly in order of likelihood on a corporate-managed Windows laptop:

1. **An endpoint-security/TLS-inspection agent** (common on corporate machines) has a root certificate installed in the Windows certificate store that Python's bundled `certifi` package doesn't know about — Python's `ssl`/`httpx` don't consult the OS store by default. Fix: `pip install pip-system-certs truststore` in the same environment (pip-system-certs depends on `truststore`; if you skip `--no-deps`, both install together — if you use `--no-deps` for some reason, install `truststore` explicitly too, or you'll see `pip_system_certs: ERROR: truststore not available`). This makes Python trust the same store the OS/browser already does — it is not a bypass, it's completing legitimate trust.
2. **A shared/global Python install with conflicting `opentelemetry-*` package versions** from another project (pip will warn about this explicitly on install) can produce confusing transport errors. Rule this out with a clean, dedicated virtualenv for the target repo before concluding it's a certificate issue.
3. **A stale `certifi` bundle** missing a newer intermediate/root cert. `pip install -U certifi` is a legitimate, low-risk fix to try — but confirm the version actually changes; if it reports "already satisfied" at a recent version, this isn't the cause.
4. **A genuine network/proxy block** on the domain (less likely if the user reports Langfuse has worked from another machine/project — that rules out an org-wide policy block specifically).

Confirm the fix worked with a real round-trip, not just "the SDK call didn't throw": push a prompt via `create_prompt`/the prompt-push script, and separately open a span, add a score, and call the client's flush method, then check the exception log/exit code from that flush — a batched OTel exporter can fail silently in the background otherwise (see Phase F's validation requirements).

## A note on judgment, not just steps

If the codebase has an unusual architecture — say, LLM calls happening inside a background worker with no natural request/response boundary, or a multi-process setup where trace context needs explicit propagation — the mechanical steps above won't map cleanly. Work out the shape of the actual call graph first rather than forcing decorators onto code that doesn't fit the pattern; a trace that's silently missing half its spans is worse than an honest "this needs custom propagation code, here's why."
