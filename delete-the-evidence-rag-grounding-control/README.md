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

A grounding checker compares a RAG answer with the retrieved document and judges
whether the answer is supported. On RAGTruth hallucinations, it performs well.
But those hallucinations are often large invented passages, with a median of
about 134 unsupported characters.

These experiments ask what happens when the unsupported claim is small.

### The data

The QA subset of the test split of
[`wandb/RAGTruth-processed`](https://huggingface.co/datasets/wandb/RAGTruth-processed)
(MIT), seed 0. Each experiment takes 100 answers annotators marked clean, so the
starting point is always a grounded answer, and edits one thing.

### The score

This experiment uses `KRLabsOrg/lettucedect-base-modernbert-en-v1` with token
output. Each answer gets one score: the highest token probability. An answer is
flagged when that score is above `0.5`.

### The edits

- `run_numbers.py`: changes one digit of a grounded number to a value absent from
  the source, about 2 characters.
- `run_negation.py`: inserts a negation into a supported sentence, about 4
  characters.

## Findings

| Unsupported claim | size | flagged |
| --- | ---: | ---: |
| invented passage (RAGTruth's own) | ~134 chars | 75 of 100 |
| changed number | ~2 chars | 48 of 100 |
| flipped negation | ~4 chars | 17 of 100 |
| nothing changed | 0 | 13 of 100 |

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
