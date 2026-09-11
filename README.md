# ai-lens

Jaison's personal Claude Code plugin marketplace. One plugin published so far:

| Plugin | What it does |
|---|---|
| [`scan-codebase-observability`](plugins/scan-codebase-observability/README.md) | Instruments a codebase for LLM/agent observability with Langfuse, and builds goal-driven custom evals — even when no labeled/golden dataset exists yet. |

## Installing from this marketplace

In Claude Code:

```
/plugin marketplace add jaison-samuel-d/ai-lens
/plugin install scan-codebase-observability@ai-lens
```

Each plugin still needs its own one-time setup (API keys, dependencies) —
see that plugin's own README under `plugins/<name>/`.

## Adding another plugin to this marketplace

1. Create `plugins/<new-plugin-name>/` with its own `.claude-plugin/plugin.json`
   (and whatever `skills/`, `agents/`, `hooks/`, `.mcp.json` it needs — only
   the pieces it actually uses).
2. Add an entry for it to `.claude-plugin/marketplace.json`'s `plugins` array,
   with `"source": "./plugins/<new-plugin-name>"`.
