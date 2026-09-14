"""Produce every table the article quotes, from results.jsonl.

Three quantities, on the same 100 cases:
  provider spread   how far apart providers of one model are (prompt held fixed)
  endpoint noise    how much one pinned provider moves between runs at temperature=0
  prompt effect     the thing the A/B was built to measure
Plus a bootstrap giving the standard error of the A/B gap at various eval sizes,
which is the table a reader uses to size their own experiment.
"""

import json
import random
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN = "deepinfra/fp8"
# Three runs per condition, everywhere. deepinfra picked up two extra prompt-A
# runs while patching a credit failure; using them would leave one provider
# measured more precisely than the rest for no reason a reader could follow.
RUNS = (0, 1, 2)
random.seed(0)


def load():
    return [json.loads(l) for l in (ROOT / "results.jsonl").read_text().splitlines() if l.strip()]


def pct(n, total):
    return 100 * n / total


def main():
    rows = load()
    cases = [json.loads(l)["id"] for l in (ROOT / "cases.jsonl").read_text().splitlines() if l.strip()]
    n = len(cases)

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

    print(f"\n=== ENDPOINT NOISE (same provider, temperature=0, between runs) ===")
    print(f"    share of cases whose answer changed across the {len(RUNS)} runs")
    for p in providers:
        repeats = sorted(sweep[p])
        if len(repeats) < 2:
            continue
        both = [c for c in cases if all(c in sweep[p][i] for i in repeats)]
        flipped = sum(1 for c in both if len({sweep[p][i][c] for i in repeats}) > 1)
        print(f"  {p:22} {flipped:3d}/{len(both)} cases changed answer ({pct(flipped, len(both)):.0f}%)")

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

    unpinned = defaultdict(lambda: defaultdict(dict))
    served = Counter()
    for r in rows:
        if r["condition"] == "unpinned":
            if r.get("error"):
                continue
            unpinned[r["prompt"]][r["repeat"]][r["case_id"]] = r["correct"]
            served[r.get("provider_served")] += 1

    if unpinned:
        print(f"\n=== UNPINNED A/B (identical code, repeated) ===")
        gaps = []
        for i in sorted(unpinned["A"]):
            a = pct(sum(unpinned["A"][i].values()), n)
            b = pct(sum(unpinned["B"][i].values()), n)
            gaps.append(b - a)
            print(f"  run {i}:  A {a:5.1f}%   B {b:5.1f}%   gap {b-a:+5.1f}pp")
        print(f"  -> gap swing across runs: {max(gaps)-min(gaps):.1f}pp"
              f"   sign reverses: {'YES' if min(gaps) < 0 < max(gaps) else 'no'}")
        total = sum(served.values())
        print(f"\n  who served {total} unpinned requests:")
        for name, count in served.most_common():
            print(f"    {str(name):22} {count:4d}  {pct(count, total):.0f}%")

    # Bootstrap: how big does an eval have to be to see a 5pp effect?
    if arms["B"]:
        rate_a = {c: st.mean([arms["A"][i][c] for i in arms["A"]]) for c in cases}
        rate_b = {c: st.mean([arms["B"][i][c] for i in arms["B"]]) for c in cases}

        def standard_error(n_cases, n_runs, trials=3000):
            diffs = []
            for _ in range(trials):
                picked = [random.choice(cases) for _ in range(n_cases)]
                a = st.mean([sum(random.random() < rate_a[c] for _ in range(n_runs)) / n_runs for c in picked])
                b = st.mean([sum(random.random() < rate_b[c] for _ in range(n_runs)) / n_runs for c in picked])
                diffs.append((b - a) * 100)
            return st.stdev(diffs)

        print("\n=== HOW BIG DOES YOUR EVAL NEED TO BE? ===")
        print("standard error of the measured A/B gap, in percentage points")
        header = "".join(f"{str(r) + ' run' + ('s' if r > 1 else ''):>10}" for r in (1, 3, 10))
        print(f"{'cases':>7}{header}")
        for size in (20, 45, 100, 300, 1000):
            cells = "".join(f"{standard_error(size, r):>10.1f}" for r in (1, 3, 10))
            print(f"{size:>7}{cells}")
        print("\na 5pp effect needs SE <= 2.5pp to be called real")


if __name__ == "__main__":
    main()
