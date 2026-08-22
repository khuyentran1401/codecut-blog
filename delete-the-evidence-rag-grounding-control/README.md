# Small Hallucinations Slip Past Your Grounding Checker

Companion code for the article *Small Hallucinations Slip Past Your Grounding
Checker*.

## How to run

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python datasets lettucedetect
```

Everything runs on CPU. No API key, no served model, no GPU.

```bash
python run_numbers.py --stage build      # construct the pairs, seconds
python run_numbers.py --stage score      # ~2 min
python run_numbers.py --stage report

python run_negation.py --stage build
python run_negation.py --stage score     # ~2 min
python run_negation.py --stage report

python run_sentences.py --stage score    # ~4 min, reuses the negation pairs
python run_sentences.py --stage edited   # ~1 min
python run_sentences.py --stage report
```

`run_sentences.py` reuses `results/negation_pairs.json`, so run `run_negation.py`
first.

`run_numbers.py` and `run_negation.py` take `--n` (sample size, default 100) and
`--seed` (default 0) on the `build` stage. `run_sentences.py` takes only `--stage`.

## Experiment design

### The question

A grounding checker compares a RAG answer against the retrieved document and
reports how much of the answer the document fails to support. On RAGTruth's own
hallucinations it does well. Those hallucinations are mostly sizeable invented
passages, averaging about 134 characters of unsupported text.

These experiments ask what happens when the unsupported claim is small.

### The data

The QA subset of the test split of
[`wandb/RAGTruth-processed`](https://huggingface.co/datasets/wandb/RAGTruth-processed)
(MIT), seed 0. Each experiment takes 100 answers annotators marked clean, so the
starting point is always a grounded answer, and edits one thing.

### The score

`KRLabsOrg/lettucedect-base-modernbert-en-v1`, token output, one score per answer
as the highest single token probability. Flagged means above `0.5`.

Token output rather than spans: a span is a run of tokens already above `0.5`, so
counting spans bakes in that threshold, and a small edit that lifts its tokens
without crossing it vanishes from the count. On the number test a flagged span
covered the changed number 34 times against 48 for the token score.

### The edits

| Script | Edit | Size |
| --- | --- | --- |
| `run_numbers.py` | one digit of a grounded number, new value absent from the source | ~2 chars |
| `run_negation.py` | a negation inserted into a supported sentence | ~4 chars |

Both edits are spliced at absolute offsets so the rest of the answer stays
byte-identical. Rebuilding an answer from a sentence list also normalizes
whitespace, and newlines turning into spaces is a second change the checker
reacts to.

## Findings

### Detection tracks the size of the claim, not its severity

| Unsupported claim | size | flagged |
| --- | ---: | ---: |
| invented passage (RAGTruth's own) | ~134 chars | 75 of 100 |
| changed number | ~2 chars | 48 of 100 |
| flipped negation | ~4 chars | 17 of 100 |
| nothing changed | 0 | 13 of 100 |

A flipped negation reverses the meaning of a claim completely and is caught
barely above the rate at which untouched answers are flagged. The 75 comes from
the article, which scores the corpus sample directly.

### A smaller scoring window does not help

Scoring each sentence separately, on the same 100 answers as the negation test:

| Scored as | negation caught | clean answer flagged |
| --- | ---: | ---: |
| one whole answer | 17 of 100 | 13 of 100 |
| worst of its sentences | 24 of 100 | 23 of 100 |
| the edited sentence alone | 13 of 100 | 10 of 100 |

Isolating the exact edited sentence, the most favorable case available, is worse
than scoring the whole answer. Lowering the threshold does not help for negation
either; every step down buys roughly as many false alarms as catches. The number
case differs, and `FINDINGS.md` keeps the two sweeps apart.

### The checker registers the flip and the output discards it

How often the flipped copy outscored its own clean twin, where chance is 50:

| Scored as | ranked higher |
| --- | ---: |
| one whole answer | 68 of 100 |
| worst of its sentences | 36 of 100 |
| the edited sentence alone | 78 of 100 |

The signal is present and consistent. It is far too small to cross a threshold
that also keeps clean answers quiet, and ranking against a known-correct twin is
not something production has.

## Files

| Path | What it holds |
| --- | --- |
| `run_numbers.py` | Change one digit of a grounded number |
| `run_negation.py` | Flip one negation in a supported sentence |
| `run_sentences.py` | Whether a smaller scoring window helps, and the paired ranking |
| `FINDINGS.md` | Run environment, what was ruled out, and scope limits |
| `results/numbers_summary.md` | Wrong-number results, with per-pair examples |
| `results/negation_summary.md` | Flipped-negation results, with per-pair examples |
| `results/sentences_summary.md` | Scoring-window results, threshold sweep, paired ranking |

Each summary is generated by its script's `--stage report`. The `build` and
`score` stages also write JSON holding every pair and every raw score, which is
where the summaries come from. Those files are a few hundred KB each and are not
committed, since seed 0 makes them reproduce exactly.
