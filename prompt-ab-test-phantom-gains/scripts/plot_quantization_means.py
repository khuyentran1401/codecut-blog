"""Chart mean score against declared quantization for the three providers that declare one.

The axis is three points wide, which is the run-to-run spread a single pinned provider shows
elsewhere in this experiment. That keeps the reader from reading the one-point gap between these
means as a real difference, without the dead space a wider borrowed axis leaves.

    uv run --with matplotlib python scripts/plot_quantization_means.py
"""

import collections
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / ".claude/skills/create-chart/scripts"))
from chart_theme import load_theme

RUNS = (0, 1, 2)
# Only these providers declare a quantization on their OpenRouter endpoint.
QUANTIZATION = {
    "relace/fp4": "fp4",
    "open-inference/fp8": "fp8",
    "deepinfra/fp8": "fp8",
}


def means_by_provider(rows):
    tally = collections.defaultdict(collections.Counter)
    for row in rows:
        if (
            row["condition"] == "sweep"
            and row["prompt"] == "A"
            and row["repeat"] in RUNS
            and row["provider_requested"] in QUANTIZATION
        ):
            tally[row["provider_requested"]][row["repeat"]] += int(bool(row["correct"]))
    return {
        name: sum(runs[r] for r in RUNS) / len(RUNS) for name, runs in tally.items()
    }


def main():
    rows = [json.loads(line) for line in (ROOT / "results.jsonl").open()]
    means = means_by_provider(rows)

    order = sorted(means, key=means.get)  # ascending, so the highest lands on top
    for name in reversed(order):
        print(f"{name:20} {means[name]:.1f}  {QUANTIZATION[name]}")

    theme = load_theme("codecut")
    fig, ax = plt.subplots(figsize=(8.4, 3.0))

    ax.scatter(
        [means[name] for name in order],
        range(len(order)),
        s=130,
        color=theme.color(0),
        edgecolors=theme.background,
        linewidths=2,
        zorder=2,
    )
    for y, name in enumerate(order):
        ax.annotate(
            f"{means[name]:.1f}",
            xy=(means[name], y),
            xytext=(14, 0),
            textcoords="offset points",
            va="center",
            color=theme.ink,
            fontfamily=theme.font,
            fontsize=theme.size("value", 11),
            clip_on=False,
        )
        ax.annotate(
            QUANTIZATION[name],
            xy=(1.0, y),
            xycoords=("axes fraction", "data"),
            xytext=(24, 0),
            textcoords="offset points",
            va="center",
            color=theme.muted,
            fontfamily=theme.font,
            fontsize=theme.size("tick", 11),
        )

    ax.set_yticks(range(len(order)), order)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlim(79, 82)
    ax.set_xticks(range(79, 83))
    ax.set_xlabel("Mean cases correct out of 100, three runs each")
    ax.set_title("Quantization did not sort the three providers", pad=32)
    ax.annotate(
        "declared",
        xy=(1.0, len(order) - 0.4),
        xytext=(24, 4),
        xycoords=("axes fraction", "data"),
        textcoords="offset points",
        va="bottom",
        color=theme.muted,
        fontfamily=theme.font,
        fontsize=theme.size("tick", 11),
    )

    theme.apply(ax, grid_axis="x")
    theme.layout(fig, left=0.26, right=0.80, top=0.78, bottom=0.26)

    out = ROOT.parents[1] / "articles/images/prompt-tweak-score-gain/quantization-means.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    theme.save(fig, out)


if __name__ == "__main__":
    main()
