# i-have-adhd plugin: default vs plugin A/B

Transcripts and harness for the experimental-evaluation brief at
`topics/i-have-adhd-plugin-output-ab.md`.

Side-by-side outputs with per-case observations are in **`OUTPUTS.md`**. This file covers
method, environment, and what the numbers mean.

## What was run

Three prompts, two conditions, five runs each. 30 transcripts in `transcripts/`.

- **`off`**: plugin disabled by removing `~/.claude/.i-have-adhd-always`
- **`on`**: sentinel present, so the plugin's SessionStart hook injects its ruleset


Both conditions used the same command:

```bash
claude -p "$prompt" \
  --permission-mode acceptEdits \
  --settings '{"outputStyle":"default",
               "enabledPlugins":{"learning-output-style@claude-plugins-official":false}}' \
  < /dev/null
```

- `claude -p`: runs Claude Code in print mode, so each prompt produces one response and exits.
- `--permission-mode acceptEdits`: keeps permission behavior consistent across runs.
- `outputStyle: "default"`: keeps both conditions on Claude Code's default output style.
- `learning-output-style@claude-plugins-official: false`: disables another style plugin that could affect the output.

Environment: Claude Code 2.1.251, Claude Opus 5, macOS 25.6, Apple M5 Pro. Run 2026-09-04.

## Cases

| ID | Prompt |
| --- | --- |
| Prompt 1 | "My model accuracy dropped after I retrained it on the new data. What should I look at?" |
| Prompt 2 | "Our nightly ETL job started taking 3 hours instead of 40 minutes. Where should I start looking?" |
| Prompt 3 | "Explain the difference between `.apply()` and vectorized operations in pandas, and when `.apply()` is actually the right choice. I want enough detail to decide." |

## Results

Medians of five runs per condition:

| Case | Prose words | Non-blank lines | List items | Ends with a next action |
| --- | --- | --- | --- | --- |
| Prompt 1 | 323 to 170 (-47%) | 19 to 8 | 13 to 5 | 0/5 to 5/5 |
| Prompt 2 | 257 to 222 (-14%) | 26 to 17 | 13 to 5 | 0/5 to 5/5 |
| Prompt 3 | 426 to 359 (-16%) | 61 to 50 | 5 to 8 | 0/5 to 5/5 |

## Files

| Path | Contents |
| --- | --- |
| `OUTPUTS.md` | The three case pairs in full, with per-case observations |
| `cases.txt` | The three prompts, one `ID\|prompt` record per line |
| `transcripts/` | The 30 runs, `{case}_{condition}_{run}.txt` |
| `results.csv` | Scored metrics, one row per transcript |
| `run_ab.sh` | The runner. Backs up and restores the sentinel file |
