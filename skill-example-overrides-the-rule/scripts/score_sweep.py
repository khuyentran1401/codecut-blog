"""Score the sweep on one question: did the commit message have a body?"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = re.compile(r"^```[a-z]*\n(.*?)\n```$", re.S)


def clean(output):
    stripped = output.strip()
    match = FENCE.match(stripped)
    return match.group(1).strip() if match else stripped


def has_body(output):
    return len([line for line in clean(output).splitlines() if line.strip()]) > 1


def main():
    rows = [json.loads(line) for line in (ROOT / __import__("os").environ.get("RESULTS","results-session.jsonl")).read_text().splitlines() if line]

    cell = defaultdict(lambda: defaultdict(int))
    total = defaultdict(lambda: {"body": 0, "n": 0})
    for row in rows:
        key = (row["turns"], row["kind"])
        total[key]["n"] += 1
        total[key]["body"] += has_body(row["output"])
        cell[key][row["case"]] += has_body(row["output"])

    print("Commit messages that came back with a body, out of 25 runs per row")
    print("(skill file identical in every row: rule says one line, all 4 examples show one line)\n")
    print(f"{'prior turns':>11}  {'history':9} {'with a body':>12}  {'rate':>6}  per case a1..a5")
    for kind in ("conflict", "clean"):
        for turns in sorted({t for t, k in total if k == kind}):
            stats = total[(turns, kind)]
            per = " ".join(f"{cell[(turns, kind)][c]}/5" for c in ("a1", "a2", "a3", "a4", "a5"))
            bar = "#" * round(20 * stats["body"] / stats["n"])
            print(f"{turns:>11}  {kind:9} {stats['body']:>8}/{stats['n']:<4} "
                  f"{stats['body'] / stats['n']:>6.2f}  {per}  {bar}")
        print()


if __name__ == "__main__":
    main()
