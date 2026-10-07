"""Regrade the stored router answers several times and report verdict flips.

Confirms planted bug 4 (a grader that gives different verdicts on the same output)
actually exists before the eval is handed to the skill.
"""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parents[1] / "eval"
sys.path.insert(0, str(EVAL_DIR))

from grader import PASS_SCORE, grade  # noqa: E402

REGRADES = 3
WORKERS = 5


def regrade(row: dict) -> dict:
    scores = [grade(row["email"], row["expected"], row["answer"])["score"] for _ in range(REGRADES)]
    return {"id": row["id"], "answer": row["answer"].splitlines()[0], "scores": [row["score"], *scores]}


def main() -> None:
    rows = [json.loads(line) for line in (EVAL_DIR / "results.jsonl").read_text().splitlines()]
    with ThreadPoolExecutor(WORKERS) as pool:
        regraded = list(pool.map(regrade, rows))

    flipped = 0
    for row in regraded:
        verdicts = {score >= PASS_SCORE for score in row["scores"]}
        flipped += len(verdicts) > 1
        print(f"{row['id']}  scores={row['scores']}  {'FLIP' if len(verdicts) > 1 else ''}  {row['answer']}")
    print(f"\ncases whose pass/fail changed across {REGRADES + 1} gradings: {flipped}/{len(regraded)}")


if __name__ == "__main__":
    main()
