# Phase D — Select custom metrics, driven by the stated goal

This is a menu, not a checklist. Building every metric below regardless of relevance produces noise, not signal, and burns judge-model budget on evaluators nobody will look at. For each candidate, ask: does this actually connect to the goal the user stated? If you can't articulate that connection in one sentence, leave it out.

Each row notes whether it's typically an **LLM-as-judge** evaluator (needs a rubric prompt — see phase-d2) or a **code evaluator** (deterministic, no judge model). Most rows are reference-free by design — they don't need a golden/labeled answer, only the rubric or the deterministic check itself. Only "answer correctness vs. a reference" genuinely requires one; that's flagged below.

## RAG / retrieval quality (if the codebase retrieves context)
- Context precision, context recall, context relevancy — LLM-as-judge or a RAGAS-style code evaluator against retrieved chunks. Reference-free.
- Faithfulness / groundedness (answer vs. retrieved context) — LLM-as-judge. Reference-free — only needs the context, not a golden answer.
- Answer relevancy — LLM-as-judge. Reference-free.
- Answer correctness (vs. a reference answer) — LLM-as-judge. **Needs a reference answer** — only build this where one genuinely exists; don't fabricate one.
- Citation accuracy — code evaluator (does the cited source actually contain the claim). Reference-free.
- Chunk utilization rate — code evaluator (retrieved-but-unused chunks). Reference-free.

## Agent / tool use (if the codebase orchestrates tools or multi-step agent loops)
- Tool selection accuracy, tool argument correctness — code evaluator against expected schema/intent, or LLM-as-judge for ambiguous cases. Reference-free.
- Tool-call success rate, redundant/repeated-call rate — code evaluator over trace spans. Reference-free.
- Plan adherence / step efficiency — LLM-as-judge (reference-free, judged as "did this look efficient") or code evaluator against a reference plan (needs one).
- Task / sub-goal completion rate — LLM-as-judge against the stated goal. Reference-free.
- Error-recovery rate, loop/deadlock detection — code evaluator over trace spans. Reference-free.

## Output quality & safety (broadly applicable)
- Hallucination rate, factual consistency — LLM-as-judge, checked against retrieved context/tool output rather than a golden answer. Reference-free.
- Toxicity / safety-violation rate — LLM-as-judge or an existing moderation model as evaluator. Reference-free.
- PII-leakage rate — code evaluator (pattern/entity check on output) — also serves as an ongoing sanity check that Phase B's masking is actually holding. Reference-free.
- False-refusal vs. appropriate-refusal rate — LLM-as-judge. Reference-free.
- Format/schema compliance — code evaluator (schema validation). Reference-free.
- Output consistency/variance across repeated runs — code evaluator (sample N runs, measure divergence). Reference-free.

## Business / goal-specific
- Whatever the stated end goal names directly — resolution rate, escalation-to-human rate, conversion impact, whatever is actually the point of the application. Define this per-goal; it will not appear in any generic taxonomy. This category is usually the one that matters most and gets the least attention by default — don't let it become an afterthought next to the generic RAG/agent metrics above.

## Efficiency / cost composites
- Cost-per-successful-task (cost score ÷ task-success score) — derived, code evaluator. Reference-free.
- Quality-per-second (latency-adjusted quality) — derived, code evaluator. Reference-free.
- Token efficiency (tokens per successful task) — derived, code evaluator. Reference-free.
- Judge-evaluator meta-cost (the cost of running the evaluators themselves) — derived, code evaluator. Track this separately; it's easy to lose track of and it's a real budget line (see `references/security-production.md`, cost governance).

## Regression / drift
- Score delta vs. previous prompt version, vs. previous model version — code evaluator comparing Experiment runs.
- Evaluator calibration health (judge-vs-human agreement rate) — code evaluator over annotation-queue overlap. Feeds Phase D3's "provisional vs. calibrated" distinction.

## Human-in-the-loop
- Annotation queue turnaround time, % of traces requiring human review — code evaluator over queue metadata.

## Operational meta-metrics (about the observability system itself, not the app)
- Instrumentation coverage % (entry points instrumented / total) — computed at scan time from Phase A's output, not per-trace.
- Eval coverage % (traces scored / total traces) — computed from the sampling config chosen in Phase D3.

## After selecting metrics

Hand the selected list to Phase D2 (prompt generation for the judge-based ones) and Phase D3 (the tiered strategy for running them without requiring a dataset up front).
