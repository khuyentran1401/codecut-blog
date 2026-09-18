"""Chart each pinned provider's three run scores, to show level and spread together.

One row per provider, one dot per run, a line spanning the provider's range. Runs that scored the
same are offset slightly so a repeated value still reads as two runs.

    uv run --with matplotlib python scripts/plot_provider_runs.py
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
TIE_OFFSET = 0.17  # vertical nudge so two runs at the same score stay countable


def scores_by_provider(rows):
    """Correct-case counts per provider per run, for the prompt A sweep."""
    tally = collections.defaultdict(collections.Counter)
    for row in rows:
        if (
            row["condition"] == "sweep"
            and row["prompt"] == "A"
            and row["repeat"] in RUNS
        ):
            tally[row["provider_requested"]][row["repeat"]] += int(bool(row["correct"]))
    return {name: [runs[r] for r in RUNS] for name, runs in tally.items()}


def tie_offsets(values):
    """A y offset per value, spreading any repeated score symmetrically around the row."""
    seen = collections.Counter()
    total = collections.Counter(values)
    offsets = []
    for value in values:
        count = total[value]
        index = seen[value]
        seen[value] += 1
        offsets.append((index - (count - 1) / 2) * TIE_OFFSET * 2)
    return offsets


def main():
    rows = [json.loads(line) for line in (ROOT / "results.jsonl").open()]
    by_provider = scores_by_provider(rows)

    order = sorted(by_provider, key=lambda name: sum(by_provider[name]) / len(RUNS))
    for name in reversed(order):
        runs = by_provider[name]
        print(f"{name:20} {runs}  mean {sum(runs) / len(RUNS):5.1f}  spread {max(runs) - min(runs)}")

    theme = load_theme("codecut")
    fig, ax = plt.subplots(figsize=(8.4, 4.2))

    for y, name in enumerate(order):
        runs = by_provider[name]
        ax.plot(
            [min(runs), max(runs)],
            [y, y],
            color=theme.grid,
            linewidth=2,
            solid_capstyle="round",
            zorder=1,
        )
        ax.scatter(
            runs,
            [y + offset for offset in tie_offsets(runs)],
            s=110,
            color=theme.color(0),
            edgecolors=theme.background,
            linewidths=2,
            zorder=2,
        )
        ax.annotate(
            f"{max(runs) - min(runs)}",
            xy=(1.0, y),
            xycoords=("axes fraction", "data"),
            xytext=(14, 0),
            textcoords="offset points",
            va="center",
            color=theme.ink,
            fontfamily=theme.font,
            fontsize=theme.size("value", 11),
        )

    ax.set_yticks(range(len(order)), order)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlim(74, 86)
    ax.set_xticks(range(74, 87, 2))
    ax.set_xlabel("Cases correct out of 100, one dot per run")
    # Pad clears the "spread" column header, which sits above the top row.
    ax.set_title("Every pinned provider moved across its own three runs", pad=32)
    ax.annotate(
        "spread",
        xy=(1.0, len(order) - 0.4),
        xycoords=("axes fraction", "data"),
        xytext=(14, 4),
        textcoords="offset points",
        va="bottom",
        color=theme.muted,
        fontfamily=theme.font,
        fontsize=theme.size("tick", 11),
    )

    theme.apply(ax, grid_axis="x")
    theme.layout(fig, left=0.26, right=0.88, top=0.82)

    out = ROOT.parents[1] / "articles/images/prompt-tweak-score-gain/provider-run-spread.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    theme.save(fig, out)


if __name__ == "__main__":
    main()
