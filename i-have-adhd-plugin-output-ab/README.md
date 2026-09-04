# i-have-adhd plugin: default vs plugin A/B

Transcripts and harness for the experimental-evaluation brief at
`topics/i-have-adhd-plugin-output-ab.md`.

Side-by-side outputs with per-case observations are in **`OUTPUTS.md`**. This file covers
method, environment, and what the numbers mean.

## What was run

Three prompts, two conditions, five runs each. 30 transcripts in `transcripts/`.

- **`off`**: plugin disabled by removing `~/.claude/.i-have-adhd-always`
- **`on`**: sentinel present, so the plugin's SessionStart hook injects its ruleset
- Both arms: `claude -p`, `--permission-mode acceptEdits`, `outputStyle` pinned to
  `default`, `learning-output-style@claude-plugins-official` disabled, a fresh working
  directory per run, no resumed context.

Environment: Claude Code 2.1.251, Claude Opus 5, macOS 25.6, Apple M5 Pro. Run 2026-09-04.

Both arms were verified rather than assumed. Asked directly whether the ADHD ruleset was
in context, the `on` arm quoted rule 1 verbatim and the `off` arm answered NO.

## Cases

| ID | Prompt | Rules under test |
| --- | --- | --- |
| F1 | "My model accuracy dropped after I retrained it on the new data. What should I look at?" | 9 (five ranked beats ten unranked), 3 (end with one next action) |
| F2 | "Our nightly ETL job started taking 3 hours instead of 40 minutes. Where should I start looking?" | 9, 3, 1 (lead with the next action) |
| F3 | "Explain the difference between `.apply()` and vectorized operations in pandas, and when `.apply()` is actually the right choice. I want enough detail to decide." | Exception 1 (explain fully when asked), the control |

F1 and F2 are diagnostic questions with no single right answer, the shape where the
default enumerates possibilities at length. F3 asks for depth outright and exists to check
that the plugin stops compressing when detail is what was requested.

## Results

Medians of five runs per condition:

| Case | Prose words | Non-blank lines | List items | Bullets | Numbered | Ends with a next action |
| --- | --- | --- | --- | --- | --- | --- |
| F1 | 323 to 170 (-47%) | 19 to 8 | 13 to 5 | 10 to 0 | 4 to 5 | 0/5 to 5/5 |
| F2 | 257 to 222 (-14%) | 26 to 17 | 13 to 5 | 13 to 0 | 0 to 5 | 0/5 to 5/5 |
| F3 | 426 to 359 (-16%) | 61 to 50 | 5 to 8 | 0 to 3 | 0 to 5 | 0/5 to 5/5 |

Three things the numbers show:

1. **The consistent change is structural, not length.** A closing next action appears in
   15 of 15 plugin runs and 0 of 15 default runs. Word count moves by -47%, -14%, and
   -16%, which is not one effect size.
2. **Thirteen unranked bullets become exactly five ranked steps.** On F1 and F2 the
   plugin returns five numbered items in every single run, which is rule 9 stated
   verbatim: "Five items ranked beats ten unranked."
3. **F3 is the control and it holds.** Asked for detail, the plugin stays long while still
   adding the closing next action, so the rules are conditional rather than a length cap.

## What the effect depends on

Four cases were run and dropped, because their correct answer is short and the plugin had
nothing to rearrange:

| Dropped prompt | Default | With the plugin |
| --- | ---: | ---: |
| A pasted `KeyError` traceback | 26 words | 24 words |
| "How do I make pytest stop at the first failure?" | 17 words | 23 words |
| "`pytest` fails, look at `features.py` and tell me why" | 111 words | 90 words |
| "My pandas pipeline uses too much memory" | 130 words | 124 words |

On the file-reading case the closing next action appeared in only 2 of 5 plugin runs,
against 5 of 5 on all three kept cases. Making the agent read files does not by itself
produce a long default answer; a question with no single right answer does.

## Two harness traps worth repeating

1. **`claude -p` is already terse.** Claude Code's own system prompt asks for short
   responses, so print mode never shows the padded preamble the plugin's README
   advertises. Preamble openers appeared zero times in every run of both arms. Case
   selection has to supply the verbosity, or the test measures nothing.
2. **A third instruction source contaminated an early batch.** The
   `learning-output-style` plugin injects through its own SessionStart hook and ignores the
   `outputStyle` setting, adding "Insight" blocks to both arms. Combined with one run per
   cell, it produced a 114-to-38 word gap on a case that showed no difference at all once
   cleaned up and replicated at five runs.

A third trap is baked into the harness itself: the condition switch is a global file at
`~/.claude/.i-have-adhd-always`, so two batches running at once will silently corrupt both
arms. Run one batch at a time.

## Files

| Path | Contents |
| --- | --- |
| `OUTPUTS.md` | The three case pairs in full, with per-case observations |
| `cases.txt` | The three prompts, one `ID\|prompt` record per line |
| `transcripts/` | The 30 runs, `{case}_{condition}_{run}.txt` |
| `results.csv` | Scored metrics, one row per transcript |
| `run_ab.sh` | The runner. Backs up and restores the sentinel file |
| `repo/` | The working directory the runs used. None of the three prompts read it |
