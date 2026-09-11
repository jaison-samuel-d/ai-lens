#!/usr/bin/env python3
"""
scan_codebase.py — deterministic Phase A scanner for the scan-codebase-observability skill.

Walks a target repo and reports, as JSON:
  - language/framework fingerprint (from manifest files)
  - existing Langfuse instrumentation markers
  - existing OpenTelemetry markers
  - ad hoc eval-looking code
  - existing golden/labeled dataset directories
  - likely entry points (routes, handlers, cron/queue consumers)
  - a lightweight secret scan (flags file:line + pattern name only — never the value)

Stdlib only, no dependencies, so it runs anywhere Python 3.8+ is available.

Usage:
    python scan_codebase.py <path-to-target-repo> [--output report.json] [--max-file-bytes 1000000]

The output is meant to be read by whoever (or whatever) is running the
scan-codebase-observability skill's Phase A — treat it as ground truth for the
mechanical part of detection and layer judgment on top, not the other way
around.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", "__pycache__",
    "dist", "build", ".next", "target", "vendor", ".tox",
    "site-packages", ".mypy_cache", ".pytest_cache", ".idea", ".vscode",
    "coverage", ".terraform", ".serverless",
}

SOURCE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".kt",
    ".rb", ".php", ".rs", ".cs", ".scala", ".mjs", ".cjs",
}

MANIFEST_LANGUAGE = {
    "package.json": "Node/JavaScript",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "Pipfile": "Python",
    "go.mod": "Go",
    "pom.xml": "Java (Maven)",
    "build.gradle": "Java/Kotlin (Gradle)",
    "build.gradle.kts": "Java/Kotlin (Gradle)",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "Cargo.toml": "Rust",
    "mix.exs": "Elixir",
    "*.csproj": "C#/.NET",
}

# "Strong" patterns are syntax, not prose — a decorator, a constructor call, an env-var
# name, an attribute access. These are what set the *_already_present booleans, because
# they essentially never show up in a comment or docstring by accident.
LANGFUSE_STRONG_PATTERNS = [
    (re.compile(r"@observe\b"), "@observe decorator"),
    (re.compile(r"\bLangfuse\s*\("), "Langfuse( client construction"),
    (re.compile(r"LANGFUSE_PUBLIC_KEY"), "LANGFUSE_PUBLIC_KEY env var"),
    (re.compile(r"LANGFUSE_SECRET_KEY"), "LANGFUSE_SECRET_KEY env var"),
    (re.compile(r"LANGFUSE_HOST"), "LANGFUSE_HOST env var"),
    (re.compile(r"langfuse\.openai"), "langfuse.openai wrapper"),
    (re.compile(r"LangfuseSpanProcessor"), "LangfuseSpanProcessor (OTel-attached)"),
    (re.compile(r"^\s*(import langfuse|from langfuse)\b"), "python import"),
    (re.compile(r"""require\(['"]langfuse['"]\)|from\s+['"]langfuse['"]"""), "js/ts import"),
]

# "Mention" is the loose, prose-catching pattern — kept as weak evidence only (e.g. a
# README or comment talking *about* Langfuse), never used to decide already_present on
# its own, since it also matches docstrings/comments that just mention the word.
LANGFUSE_MENTION_PATTERN = (re.compile(r"\blangfuse\b", re.I), "langfuse mention (prose or code)")

OTEL_STRONG_PATTERNS = [
    (re.compile(r"TracerProvider"), "TracerProvider"),
    (re.compile(r"OTEL_EXPORTER_OTLP_ENDPOINT"), "OTEL_EXPORTER_OTLP_ENDPOINT"),
    (re.compile(r"trace\.get_tracer"), "trace.get_tracer"),
    (re.compile(r"^\s*(import opentelemetry|from opentelemetry)\b"), "python import"),
]
OTEL_MENTION_PATTERN = (re.compile(r"opentelemetry", re.I), "opentelemetry mention (prose or code)")

EVAL_PATTERNS = [
    (re.compile(r"\bragas\b", re.I), "ragas"),
    (re.compile(r"ground_truth", re.I), "ground_truth reference"),
    (re.compile(r"\bllm_as_judge\b", re.I), "llm_as_judge"),
    (re.compile(r"\bjudge_prompt\b", re.I), "judge_prompt"),
    (re.compile(r"\bgolden_(set|dataset)\b", re.I), "golden_set/golden_dataset reference"),
]

ENTRY_POINT_PATTERNS = [
    (re.compile(r"@app\.(get|post|put|delete|patch)\("), "FastAPI/Flask route"),
    (re.compile(r"@router\.(get|post|put|delete|patch)\("), "router-based route"),
    (re.compile(r"app\.(get|post|put|delete|patch)\("), "Express-style route"),
    (re.compile(r"func\s+\w+\(w http\.ResponseWriter"), "Go net/http handler"),
    (re.compile(r"@RestController|@RequestMapping"), "Spring REST controller"),
    (re.compile(r"exports\.handler\s*="), "AWS Lambda (Node) handler"),
    (re.compile(r"def\s+lambda_handler\("), "AWS Lambda (Python) handler"),
    (re.compile(r"@celery\.task|@shared_task"), "Celery task (queue consumer)"),
    (re.compile(r"croniter|schedule\.every\("), "cron/scheduled job"),
    (re.compile(r"def\s+main\s*\(.*\)\s*:|func\s+main\s*\("), "CLI/script entrypoint"),
]

# Deliberately conservative — flags *shape*, never the value. False positives are fine here;
# false negatives on a real committed secret are not.
SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key ID shape"),
    (re.compile(r"-----BEGIN[ A-Z]*PRIVATE KEY-----"), "private key block"),
    (re.compile(
        r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*[\"']([A-Za-z0-9_\-\/+]{16,})[\"']"
    ), "hardcoded key/secret-shaped assignment"),
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "OpenAI-style secret key shape"),
    (re.compile(r"LANGFUSE_SECRET_KEY\s*[:=]\s*[\"']sk-lf-"), "hardcoded Langfuse secret key"),
]

DATASET_DIR_NAMES = {"datasets", "golden", "fixtures", "eval_fixtures", "goldens", "test_data"}
DATASET_FILE_EXTS = {".json", ".jsonl", ".csv", ".yaml", ".yml"}


def iter_files(root: Path, max_file_bytes: int):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            try:
                if fpath.stat().st_size > max_file_bytes:
                    continue
            except OSError:
                continue
            yield fpath


def read_text(fpath: Path):
    try:
        return fpath.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError):
        return None


def scan_manifests(root: Path):
    found = []
    for name, lang in MANIFEST_LANGUAGE.items():
        if name.startswith("*"):
            continue
        p = root / name
        if p.exists():
            found.append({"file": name, "language": lang})
    # .csproj is a glob, handle separately
    for p in root.glob("*.csproj"):
        found.append({"file": p.name, "language": "C#/.NET"})
    return found


def check_langfuse_in_manifests(root: Path):
    hits = []
    pkg = root / "package.json"
    if pkg.exists():
        text = read_text(pkg) or ""
        if re.search(r'"langfuse"', text):
            hits.append({"file": "package.json", "detail": '"langfuse" dependency'})
    for name in ("requirements.txt", "pyproject.toml", "Pipfile"):
        p = root / name
        if p.exists():
            text = read_text(p) or ""
            if re.search(r"\blangfuse\b", text, re.I):
                hits.append({"file": name, "detail": "langfuse reference"})
    return hits


def scan_source(root: Path, max_file_bytes: int):
    langfuse_strong, langfuse_mentions = [], []
    otel_strong, otel_mentions = [], []
    eval_hits, entry_points, secret_hits = [], [], []

    for fpath in iter_files(root, max_file_bytes):
        rel = str(fpath.relative_to(root))
        if fpath.suffix in SOURCE_EXTS:
            text = read_text(fpath)
            if text is None:
                continue
            lines = text.splitlines()
            for lineno, line in enumerate(lines, start=1):
                for pattern, label in LANGFUSE_STRONG_PATTERNS:
                    if pattern.search(line):
                        langfuse_strong.append({"file": rel, "line": lineno, "match": label})
                if LANGFUSE_MENTION_PATTERN[0].search(line):
                    langfuse_mentions.append({"file": rel, "line": lineno})
                for pattern, label in OTEL_STRONG_PATTERNS:
                    if pattern.search(line):
                        otel_strong.append({"file": rel, "line": lineno, "match": label})
                if OTEL_MENTION_PATTERN[0].search(line):
                    otel_mentions.append({"file": rel, "line": lineno})
                for pattern, label in EVAL_PATTERNS:
                    if pattern.search(line):
                        eval_hits.append({"file": rel, "line": lineno, "match": label})
                # Entry-point kinds overlap in wording (a decorated FastAPI route also
                # matches the bare Express-style substring) — take the first match per
                # line only, so one route doesn't get double-counted under two labels.
                for pattern, label in ENTRY_POINT_PATTERNS:
                    if pattern.search(line):
                        entry_points.append({"file": rel, "line": lineno, "kind": label})
                        break
                for pattern, label in SECRET_PATTERNS:
                    if pattern.search(line):
                        # Never include the matched value itself — flag shape/location only.
                        secret_hits.append({"file": rel, "line": lineno, "pattern": label})

        # also check env-ish files by name, not just source extensions
        elif fpath.name in {".env", ".env.local", ".env.production", ".env.example"}:
            text = read_text(fpath)
            if text is None:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                for pattern, label in SECRET_PATTERNS:
                    if pattern.search(line):
                        secret_hits.append({"file": rel, "line": lineno, "pattern": label})

    return {
        "langfuse_strong": langfuse_strong,
        "langfuse_mentions": langfuse_mentions,
        "otel_strong": otel_strong,
        "otel_mentions": otel_mentions,
        "eval_hits": eval_hits,
        "entry_points": entry_points,
        "secret_hits": secret_hits,
    }


def scan_dataset_dirs(root: Path):
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        base = os.path.basename(dirpath).lower()
        if base in DATASET_DIR_NAMES or (
            "eval" in base and any(Path(f).suffix in DATASET_FILE_EXTS for f in filenames)
        ):
            structured_files = [f for f in filenames if Path(f).suffix in DATASET_FILE_EXTS]
            if structured_files:
                found.append({
                    "dir": str(Path(dirpath).relative_to(root)),
                    "structured_file_count": len(structured_files),
                    "sample_files": structured_files[:5],
                })
    return found


def main():
    parser = argparse.ArgumentParser(description="Phase A scanner for scan-codebase-observability skill")
    parser.add_argument("target", help="Path to the target codebase")
    parser.add_argument("--output", help="Write JSON report to this file instead of stdout")
    parser.add_argument("--max-file-bytes", type=int, default=1_000_000,
                         help="Skip files larger than this (default 1MB)")
    args = parser.parse_args()

    root = Path(args.target).resolve()
    if not root.exists() or not root.is_dir():
        print(json.dumps({"error": f"{root} is not a directory"}), file=sys.stderr)
        sys.exit(1)

    manifests = scan_manifests(root)
    langfuse_manifest_hits = check_langfuse_in_manifests(root)
    scan = scan_source(root, args.max_file_bytes)
    dataset_dirs = scan_dataset_dirs(root)

    report = {
        "target": str(root),
        "manifests_found": manifests,
        "langfuse_already_present": bool(langfuse_manifest_hits or scan["langfuse_strong"]),
        "langfuse_evidence": {
            "in_manifests": langfuse_manifest_hits,
            "strong_signals": scan["langfuse_strong"][:50],
            "weak_mentions_only": scan["langfuse_mentions"][:20],
            "total_strong_matches": len(scan["langfuse_strong"]),
        },
        "otel_already_present": bool(scan["otel_strong"]),
        "otel_evidence": {
            "strong_signals": scan["otel_strong"][:50],
            "weak_mentions_only": scan["otel_mentions"][:20],
            "total_strong_matches": len(scan["otel_strong"]),
        },
        "ad_hoc_eval_code_evidence": scan["eval_hits"][:50],
        "likely_entry_points": scan["entry_points"][:100],
        "entry_point_total": len(scan["entry_points"]),
        "existing_dataset_dirs": dataset_dirs,
        "potential_secrets_flagged": scan["secret_hits"],
        "notes": [
            "potential_secrets_flagged shows file:line and pattern shape only — the matched "
            "value itself is deliberately never included in this report. Treat every hit as "
            "needing human review before instrumentation proceeds.",
            "langfuse_already_present / otel_already_present are decided from *_evidence."
            "strong_signals only (decorators, constructors, env-var names, imports) — "
            "weak_mentions_only (a bare word match) is kept for visibility but deliberately "
            "not used to set these booleans, since a comment or docstring mentioning the word "
            "isn't evidence of real instrumentation. Confirm by reading the actual client-init "
            "code before deciding whether to skip Phase B's install steps either way.",
        ],
    }

    output_text = json.dumps(report, indent=2)
    if args.output:
        Path(args.output).write_text(output_text)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == "__main__":
    main()
