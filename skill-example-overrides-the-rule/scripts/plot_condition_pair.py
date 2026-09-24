"""Plot where each request stopped obeying the skill file, conflicting history against one other
condition.

Two lanes per request. A lane runs blue while every run of that request stayed a single line, is
marked at the turn it gave in, and runs accent from there on.

Usage: uv run --with matplotlib python scripts/plot_condition_pair.py --against clean
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parents[1] / ".claude/skills/create-chart/scripts"))
from chart_theme import load_theme

FENCE = re.compile(r"^```[a-z]*\n(.*?)\n```$", re.S)
IMAGES = ROOT.parents[1] / "articles/images/session-history-overrides-skill-file"
AGAINST = {
    "clean": {"lane": "clean", "file": "conflict-vs-clean.png",
              "title": "Same session length, opposite outcome"},
    "corrected": {"lane": "corrected", "file": "conflict-vs-corrected.png",
                  "title": "Correcting the agent pushed every break later"},
}

GROUP_STEP = 2.4   # vertical distance between requests
LANE_GAP = 0.8     # vertical distance between one request's lanes


def clean(output):
    stripped = output.strip()
    match = FENCE.match(stripped)
    return match.group(1).strip() if match else stripped


def has_body(output):
    return len([line for line in clean(output).splitlines() if line.strip()]) > 1


def load_runs():
    path = ROOT / os.environ.get("RESULTS", "results-session.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    bodies = defaultdict(int)
    runs = defaultdict(int)
    for row in rows:
        key = (row["kind"], row["case"], row["turns"])
        bodies[key] += has_body(row["output"])
        runs[key] += 1
    return bodies, runs


def breakpoints(bodies, runs, kind):
    """Per request: the turns tested for this condition, and the first turn every run failed."""
    turns = sorted({t for k, _, t in runs if k == kind})
    breaks = {}
    for case in sorted({c for k, c, _ in runs if k == kind}):
        failed = [t for t in turns if bodies[(kind, case, t)] == runs[(kind, case, t)]]
        breaks[case] = failed[0] if failed else None
    return turns, breaks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--against", choices=sorted(AGAINST), default="clean")
    args = parser.parse_args()
    against = AGAINST[args.against]
    kinds = [("conflict", "never corrected"), (args.against, against["lane"])]
    out = IMAGES / against["file"]

    bodies, runs = load_runs()
    conditions = {kind: breakpoints(bodies, runs, kind) for kind, _ in kinds}

    axis_turns = conditions["conflict"][0]
    for kind, label in kinds:
        turns, breaks = conditions[kind]
        print(f"{label}: tested at {turns}")
        for case, turn in breaks.items():
            print(f"  request {case}: {'never breaks' if turn is None else f'breaks at {turn}'}")

    theme = load_theme("codecut")
    index = {turn: position for position, turn in enumerate(axis_turns)}
    cases = sorted(conditions["conflict"][1])
    last = len(axis_turns) - 1

    fig, ax = plt.subplots(figsize=(8.0, 5.2))
    held, accent = theme.color(0), theme.color(1)

    top = (len(cases) - 1) * GROUP_STEP + LANE_GAP * (len(kinds) - 1)
    tick_positions, tick_labels, group_centers = [], [], []

    for group, case in enumerate(cases):
        for lane, (kind, lane_label) in enumerate(kinds):
            turns, breaks = conditions[kind]
            y = top - (group * GROUP_STEP + lane * LANE_GAP)
            start = index[turns[0]]
            broke = breaks[case]

            end = last if broke is None else index[broke]
            ax.plot([start, end], [y, y], color=held, linewidth=4, solid_capstyle="round",
                    zorder=2)
            if broke is not None:
                if end < last:
                    ax.plot([end, last], [y, y], color=accent, linewidth=4,
                            solid_capstyle="round", zorder=2)
                ax.plot([end], [y], marker="X", markersize=11, color=accent,
                        markeredgecolor=theme.background, markeredgewidth=1.5, zorder=3)

            tick_positions.append(y)
            tick_labels.append(lane_label)

        group_centers.append((case, top - (group * GROUP_STEP + LANE_GAP * (len(kinds) - 1) / 2)))


    ax.set_yticks(tick_positions)
    ax.set_yticklabels(tick_labels)
    ax.set_xticks(range(len(axis_turns)))
    ax.set_xticklabels(axis_turns)
    ax.set_xlim(-0.4, last + 0.4)
    ax.set_ylim(-0.9, top + 0.7)
    ax.set_xlabel("prior turns in the session")
    ax.set_title(against["title"], pad=16)

    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")

    handles = [
        plt.Line2D([], [], color=held, linewidth=4, label="stayed one line"),
        plt.Line2D([], [], color=accent, marker="X", markersize=10, linestyle="none",
                   markeredgecolor=theme.background, markeredgewidth=1.5, label="breaks"),
        plt.Line2D([], [], color=accent, linewidth=4, label="grew a body"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, -0.04), ncols=3,
              frameon=False, handlelength=1.6, columnspacing=1.8)

    theme.apply(ax, grid_axis="x")
    ax.spines["bottom"].set_visible(False)
    ax.spines["top"].set_visible(True)
    ax.spines["top"].set_color(theme.grid)
    ax.xaxis.labelpad = 12
    theme.layout(fig, left=0.34, right=0.96, top=0.82, bottom=0.12)

    # The request name sits in its own column at the figure's left edge, so it can never run into
    # the right-aligned lane labels however wide those get.
    to_figure = fig.transFigure.inverted()
    for case, y_data in group_centers:
        y_figure = to_figure.transform(ax.transData.transform((0, y_data)))[1]
        fig.text(0.015, y_figure, f"request {case}", ha="left", va="center", color=theme.ink,
                 fontfamily=theme.font, fontsize=theme.size("axis_label", 12))

    out.parent.mkdir(parents=True, exist_ok=True)
    theme.save(fig, out)


if __name__ == "__main__":
    main()
