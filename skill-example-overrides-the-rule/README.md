# Your session overrides your skill file

Suppose you give a model a skill file and a request.

But earlier in the same session, the model gave answers that broke the skill's rule.

When the next request comes in, does it follow the rule or copy the pattern from the conversation history?

This experiment tests that question.

## The rule under test

`skills/commit-message/SKILL.md` states one rule and shows four examples:

```text
Write the commit message as a single line, in the form `type(scope): description`.
```

## The five requests

Five change descriptions, each about a different part of a codebase:

| | Request |
| --- | --- |
| `1` | let admins impersonate a user for support |
| `2` | correct timezone handling in the daily report |
| `3` | send a welcome email after signup |
| `4` | remove the unused legacy auth module |
| `5` | warn when a password is reused |

None of them appears in the skill file or in the history. They are fixed in `cases.jsonl`.

## What was varied

The skill file never changes. What changes is the conversation the model sees before the real request arrives.

Every run sends the model three things in order:

```text
1. the skill file, as the system message        always the same
2. some number of earlier exchanges             this is what varies
3. the actual request                           one of the five above
```

Here is an example of what the model sees when it was given two earlier exchanges:

In the **conflict** condition, every answer the agent gave earlier does not follow the rule because it has a body:

```text
user:       cache user sessions in redis

assistant:  feat(session): store sessions in redis

            Sessions were held in process memory and lost on restart.
            They now persist in redis with a 30 day expiry.
            ^ has a body, breaks the rule

user:       fix the off by one in pagination

assistant:  fix(pagination): correct last page boundary

            The final page dropped one row when the total was an exact
            multiple of the page size.
            ^ has a body, breaks the rule
```

In the **clean** condition, every answer the agent gave earlier follows the rule:

```text
user:       cache user sessions in redis. Sessions were held in process
            memory and lost on restart. They now persist in redis with
            a 30 day expiry.

assistant:  feat(session): store sessions in redis
            ^ one line, obeys the rule

user:       fix the off by one in pagination. The final page dropped one
            row when the total was an exact multiple of the page size.

assistant:  fix(pagination): correct last page boundary
            ^ one line, obeys the rule
```

To keep the comparison fair, the clean condition keeps the same body text but places it in the user's messages. At two turns, both histories are 335 characters. If the rule were simply fading as the context got longer, the clean condition should fail too.

## Results

Columns `1` to `5` are the five requests above.

- ✗ the reply has a body, breaking the rule
- ✓ the reply is one line, obeying the rule

**Conflicting history**

| Prior turns | With a body | Rate | 1 | 2 | 3 | 4 | 5 |
| ---: | ---: | ---: | :-: | :-: | :-: | :-: | :-: |
| 0 | 0/25 | 0.00 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2 | 10/25 | 0.40 | ✗ | ✓ | ✓ | ✓ | ✗ |
| 4 | 15/25 | 0.60 | ✗ | ✓ | ✓ | ✗ | ✗ |
| 6 | 25/25 | 1.00 | ✗ | ✗ | ✗ | ✗ | ✗ |
| 8 | 25/25 | 1.00 | ✗ | ✗ | ✗ | ✗ | ✗ |
| 10 | 25/25 | 1.00 | ✗ | ✗ | ✗ | ✗ | ✗ |
| 15 | 25/25 | 1.00 | ✗ | ✗ | ✗ | ✗ | ✗ |
| 20 | 25/25 | 1.00 | ✗ | ✗ | ✗ | ✗ | ✗ |

**Corrected history**

| Prior turns | With a body | Rate | 1 | 2 | 3 | 4 | 5 |
| ---: | ---: | ---: | :-: | :-: | :-: | :-: | :-: |
| 2 | 0/25 | 0.00 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 6 | 0/25 | 0.00 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 10 | 0/25 | 0.00 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 20 | 10/25 | 0.40 | ✗ | ✗ | ✓ | ✓ | ✓ |

**Clean history**

| Prior turns | With a body | Rate | 1 | 2 | 3 | 4 | 5 |
| ---: | ---: | ---: | :-: | :-: | :-: | :-: | :-: |
| 10 | 0/25 | 0.00 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 20 | 0/25 | 0.00 | ✓ | ✓ | ✓ | ✓ | ✓ |

Correcting the agent delays the failure without preventing it. Never correcting breaks the rule at 6 turns, correcting every time holds until 20, and a session that was never wrong holds throughout.

Per request, the turn count at which it first breaks:

| Request | Never corrected | Corrected |
| --- | ---: | ---: |
| `1` let admins impersonate a user for support | breaks at 2 | breaks at 20 |
| `2` correct timezone handling in the daily report | breaks at 6 | breaks at 20 |
| `3` send a welcome email after signup | breaks at 6 | never breaks |
| `4` remove the unused legacy auth module | breaks at 4 | never breaks |
| `5` warn when a password is reused | breaks at 2 | never breaks |

Correcting moved every request, by different amounts. Three held out to 20 turns and two gave way there anyway.

Two things to keep in mind reading that last column:

- Corrected was only tested at 2, 6, 10 and 20 turns, so a request that survived 20 might break at 25.
- Five requests is too few to say why request 5 goes from breaking at 2 to never breaking, while request 1 still breaks.

## One request end to end

Here are the results for the request "correct timezone handling in the daily report" after 0, 6, and 20 prior turns in the conflicting-history condition.

```text
 0 turns   fix(daily-report): correct timezone handling

 6 turns   fix(reports): use UTC for daily report timestamps

           The daily report was using the local timezone, leading to
           incorrect time-based aggregations. Now using UTC consistently.

20 turns   fix(report): use UTC for daily report timestamps

           The report used the local timezone and caused
           discrepancies across regions. Now it's consistent.
```

## Files

| File | What it holds |
| --- | --- |
| `skills/commit-message/` | the skill file, unchanged in every run |
| `cases.jsonl` | the five requests |
| `scripts/induction.py` | the twenty earlier exchanges used to build the history |
| `scripts/run_sweep.py` | the runner |
| `scripts/score_sweep.py` | the body check and the tables above |
| `results-session.jsonl` | one scored row per run, the source of every number here |

## Rerun it

Needs Ollama running, with `qwen3:8b` pulled.

```bash
python3 scripts/run_sweep.py
python3 scripts/score_sweep.py
```

Environment: `qwen3:8b` through Ollama, temperature 0, thinking off, on an Apple M5 Pro. Run 2026-09-21.
