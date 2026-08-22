# Findings

Supporting detail for `README.md`: what the runs ruled out, and what the numbers
do not cover.

## Run environment

Run date: 2026-08-22. MacBook Pro, Apple M5 Pro, 18 cores, arm64. CPU only,
about 0.1 s per answer.

Python 3.11.11, `lettucedetect` 0.2.3, `datasets` 5.0.1, `transformers` 5.15.0,
`torch` 2.13.0. No script imports numpy or scikit-learn.

Sample: 100 answers per experiment from the QA subset of the
`wandb/RAGTruth-processed` test split, seed 0, all annotated clean before editing.

## What was ruled out

### The claim being small, as an explanation

The negation result invited an obvious fix: if detection tracks how much of the
text is unsupported, shrink the text. It does not work. Scoring the worst of an
answer's sentences moved catches from 17 to 24 and false alarms from 13 to 23,
and scoring the edited sentence by itself came out at 13 and 10, worse than the
whole answer on both counts.

Taking the worst sentence lands near chance on the paired ranking (36 of 100)
because the highest-scoring sentence is usually not the edited one, so the flip
never moves the number while every answer's noisiest sentence gets a vote. That
is where the extra false alarms came from.

### Threshold tuning, for negation

| threshold | negations caught | untouched answers flagged |
| ---: | ---: | ---: |
| 0.5 | 17 of 100 | 13 of 100 |
| 0.2 | 30 of 100 | 26 of 100 |
| 0.1 | 37 of 100 | 32 of 100 |
| 0.02 | 59 of 100 | 44 of 100 |

Every step down buys roughly as many false alarms as catches, so no threshold
separates a flipped negation from a clean answer.

The number case behaves differently and the two should not be conflated. There,
recall really is for sale:

| threshold | changed numbers caught | untouched answers flagged |
| ---: | ---: | ---: |
| 0.5 | 48 of 100 | 16 of 100 |
| 0.2 | 70 of 100 | 25 of 100 |
| 0.02 | 87 of 100 | 49 of 100 |

Dropping to 0.2 gains 22 catches for 9 extra false alarms. That is a real trade
rather than a wash, but it means flagging a quarter of the clean answers.

### Span count as the scoring rule

A span is a run of tokens already above `0.5`, so counting spans inherits that
threshold. On the number test a flagged span covered the changed number 34 times
against 48 for the token score, so the span view loses 14 cases the token view
keeps. Since these experiments are about small edits, the coarser output would
understate the checker.

### Whitespace as a second edit

An early version of the negation test rebuilt the answer from a sentence list,
which normalized whitespace in 32 of 100 cases. Those cases showed a 31% catch
rate against 9% for the rest, so newlines turning into spaces was doing much of
the work. Both scripts now splice edits at absolute offsets, leaving every other
byte untouched.

### Number edits detectable by shape

`run_numbers.py` rejects an edit that would introduce a leading zero, because
`05` is detectable by its shape rather than its value. It also skips values below
10 and anything from 1900 to 2100, which are list markers and years rather than
claims.

### The two edits using different answers

Each edit needs something specific to edit, so the number and negation sets are
not identical. On the 30 answers eligible for both, the ordering holds: 12 of 30
for a changed number against 6 of 30 for a flipped negation.

## Scope and limits

- **One corpus, one task type.** RAGTruth is also LettuceDetect's training
  distribution, so this is home turf for the checker. The comparisons between
  edit types are valid; the absolute rates describe this corpus.
- **Constructed edits.** A one-digit change and an inserted negation are
  diagnostics chosen for being small and unambiguous, not a sample of how real
  RAG systems fail.
- **The paired ranking is not a usable signal.** Comparing an answer against its
  own clean twin ranks the flip correctly 78 times out of 100, but production has
  no clean twin to compare against.
- **Balanced by construction.** Every experiment starts from 100 clean answers and
  edits each one, so the flagged-when-untouched column is a false-alarm rate on
  clean text, not a base rate on live traffic.
