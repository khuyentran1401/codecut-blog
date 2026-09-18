"""Chart the invented optional arguments per run for prompt A and prompt B.

An invented optional argument is a failure where the model supplied a value for an argument whose
ground truth also accepts "" (BFCL's way of saying that omitting it is correct).

    uv run --with matplotlib python scripts/plot_invented_arguments.py
"""

import collections
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / ".claude/skills/create-chart/scripts"))
from chart_theme import load_theme

PROVIDER = "deepinfra/fp8"
RUNS = (0, 1, 2)
# Prompt A ran as part of the provider sweep; prompt B ran as its own pinned condition.
CONDITIONS = {"A": "sweep", "B": "pinned"}
REASON = re.compile(r"^(\w+)=.* not acceptable")


def optional(case, arg):
    """True when the ground truth accepts "", so omitting the argument is correct."""
    for truth in case["ground_truth"]:
        for args in truth.values():
            if arg in args:
                return "" in args[arg]
    return False


def counts(rows, cases, prompt):
    per_run = collections.Counter()
    for row in rows:
        if (
            row["condition"] != CONDITIONS[prompt]
            or row["provider_requested"] != PROVIDER
            or row["prompt"] != prompt
            or row["repeat"] not in RUNS
            or row["correct"]
        ):
            continue
        match = REASON.match(str(row.get("reason", "")))
        if match and optional(cases[row["case_id"]], match.group(1)):
            per_run[row["repeat"]] += 1
    return [per_run[run] for run in RUNS]


def main():
    cases = {}
    for line in (ROOT / "cases.jsonl").open():
        case = json.loads(line)
        cases[case["id"]] = case
    rows = [json.loads(line) for line in (ROOT / "results.jsonl").open()]

    a = counts(rows, cases, "A")
    b = counts(rows, cases, "B")
    print(f"prompt A per run: {a}  total {sum(a)}")
    print(f"prompt B per run: {b}  total {sum(b)}")

    theme = load_theme("codecut")
    x = np.arange(len(RUNS))
    width = 0.3
    gap = 0.02  # keeps a sliver of background between the paired bars

    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    bars_a = ax.bar(x - (width + gap) / 2, a, width, label="Prompt A", color=theme.color(0))
    bars_b = ax.bar(x + (width + gap) / 2, b, width, label="Prompt B", color=theme.color(1))

    ax.set_title(
        "Prompt B invented fewer optional arguments, but not in every run", pad=34
    )
    ax.set_ylabel("Invented optional arguments")
    ax.set_xticks(x, [f"Run {run}" for run in RUNS])
    ax.set_ylim(0, max(a + b) + 1.2)
    ax.set_yticks(range(0, max(a + b) + 2, 2))
    theme.apply(ax)
    theme.legend_above(ax)
    theme.layout(fig, left=0.1, right=0.97, top=0.8)
    theme.label_bars(ax, bars_a)
    theme.label_bars(ax, bars_b)

    out = (
        ROOT.parents[1]
        / "articles/images/prompt-tweak-score-gain/invented-optional-arguments.png"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    theme.save(fig, out)


if __name__ == "__main__":
    main()
