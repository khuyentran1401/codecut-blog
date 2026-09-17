"""Produce the article tables from results.jsonl.

The article uses three quantities on the same 100 cases:
  provider spread   how far apart providers of one model are, with prompt fixed
  repeatability     whether pinned providers return the same score on reruns
  prompt effect     whether Prompt B beats Prompt A on one pinned provider
"""

import json
import statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN = "deepinfra/fp8"
# Three runs per condition, everywhere. deepinfra picked up two extra prompt-A
# runs while patching a credit failure; using them would leave one provider
# measured more precisely than the rest for no reason a reader could follow.
RUNS = (0, 1, 2)


def load():
    return [json.loads(l) for l in (ROOT / "results.jsonl").read_text().splitlines() if l.strip()]


def pct(n, total):
    return 100 * n / total


def main():
    rows = load()
    n = sum(1 for line in (ROOT / "cases.jsonl").read_text().splitlines() if line.strip())

    # provider -> repeat -> case -> correct
    sweep = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        if r["condition"] == "sweep" and not r.get("error") and r["repeat"] in RUNS:
            sweep[r["provider_requested"]][r["repeat"]][r["case_id"]] = r["correct"]
    providers = sorted(sweep)

    print(f"=== PROVIDER SPREAD ({n} cases, prompt A, same model id) ===")
    print(f"    {len(RUNS)} runs per provider, complete runs only")
    means = {}
    for p in providers:
        complete = [i for i in sorted(sweep[p]) if len(sweep[p][i]) == n]
        if not complete:
            print(f"  {p:22} no complete run")
            continue
        per_run = [pct(sum(sweep[p][i].values()), n) for i in complete]
        means[p] = st.mean(per_run)
        runs = "  ".join(f"{v:.0f}" for v in per_run)
        print(f"  {p:22} runs [{runs}]  mean {means[p]:5.1f}%")
    spread = max(means.values()) - min(means.values())
    print(f"  -> best minus worst provider: {spread:.1f} pp")

    # prompt arms, pinned
    arms = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        if r.get("error"):
            continue
        if r["repeat"] not in RUNS:
            continue
        if r["condition"] == "sweep" and r["provider_requested"] == PIN:
            arms["A"][r["repeat"]][r["case_id"]] = r["correct"]
        elif r["condition"] == "pinned":
            arms["B"][r["repeat"]][r["case_id"]] = r["correct"]
    for prompt in ("A", "B"):
        for i in [i for i in arms[prompt] if len(arms[prompt][i]) < n]:
            del arms[prompt][i]

    if arms["B"]:
        print(f"\n=== PROMPT EFFECT (pinned to {PIN}) ===")
        for prompt in ("A", "B"):
            per_run = [pct(sum(arms[prompt][i].values()), n) for i in sorted(arms[prompt])]
            runs = "  ".join(f"{v:.0f}" for v in per_run)
            print(f"  prompt {prompt}  runs [{runs}]  mean {st.mean(per_run):5.1f}%")
        gap = st.mean([pct(sum(arms["B"][i].values()), n) for i in sorted(arms["B"])]) - st.mean(
            [pct(sum(arms["A"][i].values()), n) for i in sorted(arms["A"])]
        )
        print(f"  -> prompt effect (B minus A): {gap:+.1f} pp")


if __name__ == "__main__":
    main()
