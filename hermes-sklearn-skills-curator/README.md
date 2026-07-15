# Hermes Skills + Curator Experiment — Artifacts

Real artifacts from testing two Hermes Agent features on a scikit-learn debugging task, entirely on a local model:

1. **Autonomous crystallization** — the agent writes a reusable `SKILL.md` on its own after a complex task, without being asked.
2. **The Curator** — a background pass that ages, archives, and (opt-in) consolidates the agent-written skills so they don't pile up.

Everything here was captured from actual runs, not written by hand.

## Setup used

- **Hermes Agent** via `curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`
- **Model**: `qwen3-coder:30b` served locally by **Ollama** (free, private, coding-tuned)
- `~/.hermes/config.yaml` model block:
  ```yaml
  model:
    default: "qwen3-coder:30b"
    provider: "ollama"
    base_url: "http://localhost:11434/v1"
    context_length: 65536
  ```

## Files

| Path | What it is |
|---|---|
| `task/data.csv` | Messy dataset: `annual_spend_usd` stored as `"1,200"` strings, missing values, categorical `respondent_region`, `converted` = yes/no |
| `task/train_buggy.py` | The naive script that fails (`could not convert string to float: 'North'`) |
| `task/train_fixed.py` | The script after the agent debugged it end to end |
| `skills/data-cleaning-for-machine-learning.SKILL.md` | **Auto-created by the agent, unprompted**, after the debug |
| `skills/sklearn-debug-v2.SKILL.md` | A related agent-authored skill |
| `skills/clean-csv-*.SKILL.md`, `prep-messy-data-sklearn.SKILL.md` | Three deliberately overlapping skills planted to test the Curator's consolidation |
| `transcripts/crystallization_session.jsonl` | Full session export of the debug run (30 messages, 14 tool calls) |
| `curator/consolidation_REPORT_qwen3-coder.md` | The Curator's LLM consolidation dry-run report (coder model) |

## The commands

```bash
# 1. Crystallization: a debug task that never mentions skills
hermes -m qwen3-coder:30b -z "In <dir>, 'python3 train.py' fails. Debug it end to end: run it, read each error, edit train.py, repeat until it trains a LogisticRegression and prints an accuracy. Inspect the actual data before assuming column types. End with the final accuracy."
hermes curator usage        # a NEW agent-created skill appeared with no request

# 2. Curator: inspect, deterministic lifecycle, consolidation preview
hermes curator status
hermes curator usage
hermes curator archive <skill>
hermes curator list-archived
hermes curator restore <skill>
hermes curator pin <skill>
hermes curator run --consolidate --dry-run   # preview merges; read the REPORT.md it writes
```

## What actually happened

- **Crystallization fired unprompted.** The prompt only asked to debug and report the accuracy. The agent fixed the script (14 tool calls) and, on its own, created `data-cleaning-for-machine-learning`. Confirmed via `hermes curator usage`.
- **The auto-created skill was solid** (captured the comma-strip, imputation, and encoding fixes), but agent-written skills should still be reviewed as drafts.
- **The Curator's deterministic lifecycle works and is safe.** `archive → list-archived → restore` and time-based aging (`active → stale → archived`, never deletes) behaved exactly as documented.
- **The Curator's LLM consolidation proved unreliable.** Across four `--consolidate --dry-run` attempts: it merged the CSV/sklearn duplicates only when they were **planted** as obvious near-duplicates (`curator/consolidation_REPORT_qwen3-coder.md`); on the genuine naturally-occurring overlap alone (`sklearn-debug-v2` vs `data-cleaning-for-machine-learning`) it **missed it** and proposed only invalid merges/prunes of **bundled** skills it is documented never to touch (`curator/consolidation_REPORT_natural-only.md`); and one run failed outright (malformed tool call, zero analysis). The Curator only ever *acts* on agent-created skills, but the raw dry-run proposal over-reaches into bundled skills and is often wrong. Treat consolidation as opt-in, always dry-run, and do not rely on it.

## Honest notes

- These are single runs on a local model, enough for a "watch it happen" field report, not for statistical claims.
- What gets *created* (skill content) and *merged* (consolidation proposal) is the model's judgment. The framework provides the machinery; you supervise the content: verify auto-written skills, and always `--dry-run` the Curator before applying.
