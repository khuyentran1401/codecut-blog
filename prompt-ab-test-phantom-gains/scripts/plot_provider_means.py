"""Chart each provider's mean score across its three runs, sorted best to worst.

Dots, not bars: the means sit between 77 and 82, so a zero baseline would render six
near-identical bars. Dots encode position, which makes a 76 to 83 axis honest rather than a
truncation.

    uv run --with matplotlib python scripts/plot_provider_means.py
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


def means_by_provider(rows):
    """Mean correct-case count per provider over the prompt A sweep runs."""
    tally = collections.defaultdict(collections.Counter)
    for row in rows:
        if (
            row["condition"] == "sweep"
            and row["prompt"] == "A"
            and row["repeat"] in RUNS
        ):
            tally[row["provider_requested"]][row["repeat"]] += int(bool(row["correct"]))
    return {
        name: sum(runs[r] for r in RUNS) / len(RUNS) for name, runs in tally.items()
    }


def main():
    rows = [json.loads(line) for line in (ROOT / "results.jsonl").open()]
    means = means_by_provider(rows)

    order = sorted(means, key=means.get)  # ascending, so the best lands on top
    for name in reversed(order):
        print(f"{name:20} {means[name]:.1f}")

    theme = load_theme("codecut")
    fig, ax = plt.subplots(figsize=(8.4, 4.2))

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

    ax.set_yticks(range(len(order)), order)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlim(76, 83)
    ax.set_xticks(range(76, 84))
    ax.set_xlabel("Mean cases correct out of 100, three runs each")
    ax.set_title("One provider sat five points below the rest", pad=14)

    theme.apply(ax, grid_axis="x")
    theme.layout(fig, left=0.26, right=0.95, top=0.86)

    out = ROOT.parents[1] / "articles/images/prompt-tweak-score-gain/provider-means.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    theme.save(fig, out)


if __name__ == "__main__":
    main()
