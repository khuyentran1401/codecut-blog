"""Scatter each provider's input price against its mean score.

Scores come from results.jsonl. Prices come from prices.json, which freezes what the six endpoints
cost when the sweep ran, because the run scripts never recorded price.

    uv run --with matplotlib python scripts/plot_price_vs_score.py
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
# Where each provider's name sits relative to its dot, to keep the six labels from colliding.
LABEL_SIDE = {
    "digitalocean": "right",
    "relace/fp4": "above",
    "together": "left",
    "open-inference/fp8": "right",
    "deepinfra/fp8": "right",
    "wafer/fast": "right",
}


def means_by_provider(rows):
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
    prices = json.loads((ROOT / "prices.json").read_text())["usd_per_million_input_tokens"]

    missing = set(means) ^ set(prices)
    if missing:
        raise ValueError(f"provider mismatch between results and prices: {sorted(missing)}")

    for name in sorted(means, key=prices.get):
        print(f"{name:20} ${prices[name]:.2f}  mean {means[name]:.1f}")

    theme = load_theme("codecut")
    fig, ax = plt.subplots(figsize=(8.4, 4.2))

    ax.scatter(
        [prices[name] for name in means],
        [means[name] for name in means],
        s=130,
        color=theme.color(0),
        edgecolors=theme.background,
        linewidths=2,
        zorder=2,
    )
    for name, mean in means.items():
        offset, align, valign = {
            "right": ((14, 0), "left", "center"),
            "left": ((-14, 0), "right", "center"),
            "above": ((0, 18), "center", "bottom"),
            "below": ((0, -18), "center", "top"),
        }[LABEL_SIDE[name]]
        ax.annotate(
            name,
            xy=(prices[name], mean),
            xytext=offset,
            textcoords="offset points",
            ha=align,
            va=valign,
            color=theme.ink,
            fontfamily=theme.font,
            fontsize=theme.size("tick", 11),
        )

    ax.set_xlim(0.03, 0.155)
    ax.set_xticks([0.04, 0.06, 0.08, 0.10, 0.12, 0.14])
    ax.set_xticklabels([f"${p:.2f}" for p in (0.04, 0.06, 0.08, 0.10, 0.12, 0.14)])
    ax.set_ylim(76, 83)
    ax.set_yticks(range(76, 84))
    ax.set_xlabel("Input price per million tokens")
    ax.set_ylabel("Mean cases correct")
    ax.set_title("Price did not predict quality", pad=14)

    theme.apply(ax, grid_axis="both")
    theme.layout(fig, left=0.1, right=0.97, top=0.87, bottom=0.16)

    out = ROOT.parents[1] / "articles/images/prompt-tweak-score-gain/price-vs-score.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    theme.save(fig, out)


if __name__ == "__main__":
    main()
