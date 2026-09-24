"""Plot the turn at which each request stopped obeying the skill file.

One lane per request, in request order. The lane runs muted while every run of that request stayed
a single line, is marked at the turn it gave in, and runs accent from there on.
"""

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
KIND = "conflict"
OUT = ROOT.parents[1] / "articles/images/session-history-overrides-skill-file/request-breakpoints.png"



def clean(output):
    stripped = output.strip()
    match = FENCE.match(stripped)
    return match.group(1).strip() if match else stripped


def has_body(output):
    return len([line for line in clean(output).splitlines() if line.strip()]) > 1


def load_breakpoints():
    """Per request: the tested turn count at which every run first grew a body."""
    path = ROOT / os.environ.get("RESULTS", "results-session.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    bodies = defaultdict(int)
    runs = defaultdict(int)
    for row in rows:
        if row["kind"] != KIND:
            continue
        key = (row["case"], row["turns"])
        bodies[key] += has_body(row["output"])
        runs[key] += 1

    turns = sorted({t for _, t in runs})
    breaks = {}
    for case in sorted({c for c, _ in runs}):
        failed = [t for t in turns if bodies[(case, t)] == runs[(case, t)]]
        breaks[case] = failed[0] if failed else None
    return turns, breaks


def main():
    turns, breaks = load_breakpoints()
    print(f"tested turn counts: {turns}")
    for case, turn in breaks.items():
        print(f"  request {case}: breaks at {turn}")

    theme = load_theme("codecut")
    index = {turn: position for position, turn in enumerate(turns)}
    cases = sorted(breaks)
    last = len(turns) - 1

    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    held = theme.color(0)
    accent = theme.color(1)

    for lane, case in enumerate(cases):
        y = len(cases) - 1 - lane
        broke = index[breaks[case]]
        ax.plot([0, broke], [y, y], color=held, linewidth=4, solid_capstyle="round",
                zorder=1)
        ax.plot([broke, last], [y, y], color=accent, linewidth=4, solid_capstyle="round",
                zorder=1)
        ax.plot([broke], [y], marker="X", markersize=11, color=accent,
                markeredgecolor=theme.background, markeredgewidth=1.5, zorder=3)

    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([f"request {c}" for c in reversed(cases)])
    ax.set_xticks(range(len(turns)))
    ax.set_xticklabels(turns)
    ax.set_xlim(-0.4, last + 0.4)
    ax.set_ylim(-0.6, len(cases) - 0.4)
    ax.set_xlabel("prior turns of conflicting history")
    ax.set_title("Every request broke within 6 prior turns", pad=16)

    # The sketch reads top down: turn counts first, then the lanes hanging off them.
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")

    handles = [
        plt.Line2D([], [], color=held, linewidth=4, label="stayed one line"),
        plt.Line2D([], [], color=accent, marker="X", markersize=10, linestyle="none",
                   markeredgecolor=theme.background, markeredgewidth=1.5, label="breaks"),
        plt.Line2D([], [], color=accent, linewidth=4, label="grew a body"),
    ]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, -0.06), ncols=3,
              frameon=False, handlelength=1.6, columnspacing=1.8)

    theme.apply(ax, grid_axis="x")
    ax.spines["bottom"].set_visible(False)
    ax.spines["top"].set_visible(True)
    ax.spines["top"].set_color(theme.grid)
    ax.xaxis.labelpad = 12
    theme.layout(fig, left=0.17, right=0.96, top=0.7, bottom=0.18)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    theme.save(fig, OUT)


if __name__ == "__main__":
    main()
