# Reasoning Mode Benchmark

This folder contains the source code and companion results for the article
[Before You Upgrade the Model, Try Thinking Mode](https://codecut.ai/before-you-upgrade-the-model-try-thinking-mode/).

The recorded prompts, expected answers, and results are in
[`all-problems.md`](all-problems.md).

## What the Script Includes

The runnable benchmark script,
[`run_reasoning_mode_benchmark.py`](run_reasoning_mode_benchmark.py), includes
all 12 prompts used in the article:

- 8 multi-step prompts
- 4 single-step prompts

Each prompt is stored with its expected answer and problem type. The script runs
each prompt in two modes:

- Plain mode: `think=False`, greedy decoding
- Thinking mode: `think=True`, Qwen's recommended thinking settings

It reports correctness and latency for both modes.

## Requirements

Install and run Ollama, then pull the model:

```bash
ollama pull qwen3:30b-a3b
```

The script expects Ollama to be running at:

```text
http://localhost:11434/api/chat
```

## Run the Full Benchmark

From the repository root:

```bash
python notebooks/reasoning-mode-before-bigger-model/run_reasoning_mode_benchmark.py
```

## Show a Thinking Trace for One Prompt

```bash
python notebooks/reasoning-mode-before-bigger-model/run_reasoning_mode_benchmark.py \
  --trace split-discrepancy \
  --trace-lines 4
```

Available trace names are the prompt names in `all-problems.md`, such as
`split-discrepancy`, `installment-fees`, and `percent-of-deposit`.
