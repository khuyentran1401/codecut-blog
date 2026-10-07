"""Run the router over every case, grade each answer, and print the score."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from grader import grade
from router import route_email

HERE = Path(__file__).parent
WORKERS = 5


def run_case(case: dict) -> dict:
    answer = route_email(case["email"])
    return {**case, "answer": answer, **grade(case["email"], case["expected"], answer)}


def main() -> None:
    cases = json.loads((HERE / "cases.json").read_text())
    with ThreadPoolExecutor(WORKERS) as pool:
        results = list(pool.map(run_case, cases))

    with open(HERE / "results.jsonl", "w") as f:
        for row in results:
            f.write(json.dumps(row) + "\n")

    passed = sum(row["passed"] for row in results)
    for row in results:
        print(f"{row['id']}  {'PASS' if row['passed'] else 'FAIL'}  score={row['score']}  {row['email'][:60]}")
    print(f"\nscore: {passed}/{len(results)} = {passed / len(results):.2f}")


if __name__ == "__main__":
    main()
