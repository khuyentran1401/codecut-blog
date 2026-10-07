"""Run the router over every case, grade each answer, and print the score.

Usage:
    python run_eval.py --variant baseline --reps 3
    python run_eval.py --variant baseline --reps 3 --limit 5   # pilot on the first 5 cases
    python run_eval.py --approve-harness ...                   # human-only: accept harness edits

Output goes to .claude/hillclimb/router/<variant>/:
    results.jsonl  one row per scored (case, rep), written as each case finishes
    traces/        full exchange per (case, rep)
    errors.jsonl   attempts that never produced a scorable answer (append-only)
Re-running the same command resumes: (case, rep) pairs already in results.jsonl are skipped.
"""

import argparse
import hashlib
import json
import math
import random
import subprocess
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from grader import grade
from router import SYSTEM_PROMPT, route_email

HERE = Path(__file__).parent
FLOW_DIR = HERE / ".claude" / "hillclimb" / "router"
STATE_PATH = FLOW_DIR / "_state.json"
WORKERS = 5
MAX_ATTEMPTS = 3
BACKOFF_BASE_S = 2.0

write_lock = threading.Lock()


class ModelMismatch(Exception):
    pass


class NoAnswer(Exception):
    """Every attempt failed before producing a scorable answer."""

    def __init__(self, errors: list[dict]):
        super().__init__(f"{len(errors)} failed attempt(s)")
        self.errors = errors


def check_harness(approve: bool) -> None:
    """Refuse to run if the runner, grader, or cases changed since a human last approved them."""
    state = json.loads(STATE_PATH.read_text())
    paths = [Path(__file__).resolve(), *(HERE / p for p in state.get("harness_paths", []))]
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode() + b"\0" + path.read_bytes())
    sha = digest.hexdigest()
    if state.get("harness_sha") == sha:
        return
    if approve:
        state["harness_sha"] = sha
        STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")
        print(f"harness approved: sha256 {sha[:12]}")
        return
    raise SystemExit(
        f"harness changed or never approved (sha256 {sha[:12]}). "
        "Review run_eval.py, grader.py, cases.json, then re-run with --approve-harness."
    )


def append_jsonl(path: Path, row: dict) -> None:
    with write_lock, open(path, "a") as f:
        f.write(json.dumps(row) + "\n")


def done_keys(results_path: Path) -> set[tuple[str, int]]:
    if not results_path.exists():
        return set()
    rows = (json.loads(line) for line in results_path.read_text().splitlines() if line.strip())
    return {(row["prompt_id"], row["rep"]) for row in rows}


def served_model(meta: dict, requested: str) -> str:
    served = list(meta.get("modelUsage") or {})
    matching = [m for m in served if requested in m]
    if not matching:
        raise ModelMismatch(f"requested {requested!r}, served {served}")
    return matching[0]


def call_router(email: str, model: str) -> tuple[str, dict, float, int]:
    """Call the real entry point, retrying transient failures with jittered backoff.

    Returns (answer, meta, latency_s, retries). Raises NoAnswer with one record per failed attempt.
    The subprocess timeout in llm.py is the hard per-call wall-clock ceiling; timeouts are not retried.
    """
    errors = []
    for attempt in range(MAX_ATTEMPTS):
        meta: dict = {}
        start = time.monotonic()
        try:
            answer = route_email(email, model=model, meta=meta)
            return answer, meta, time.monotonic() - start, attempt
        except subprocess.TimeoutExpired:
            failure = "timeout"
        except (RuntimeError, ValueError):  # CLI error reply or unparseable CLI output
            failure = "harness_error"
        errors.append({"failure_class": failure, "attempt": attempt, "model": model, "usage": meta.get("usage")})
        if failure == "timeout":
            break
        time.sleep(BACKOFF_BASE_S * 2**attempt + random.uniform(0, 1))
    raise NoAnswer(errors)


def run_case(case: dict, rep: int, model: str, out_dir: Path) -> None:
    key = {"prompt_id": case["id"], "rep": rep}
    try:
        answer, meta, latency_s, retries = call_router(case["email"], model)
        served = served_model(meta, model)
    except NoAnswer as exc:
        for err in exc.errors:
            append_jsonl(out_dir / "errors.jsonl", {**key, **err})
        return
    except ModelMismatch as exc:
        append_jsonl(out_dir / "errors.jsonl", {**key, "failure_class": "model_mismatch", "detail": str(exc),
                                                "model": model, "usage": meta.get("usage")})
        return

    trace = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": case["email"]},
        {"role": "assistant", "content": answer},
    ]
    (out_dir / "traces" / f"{case['id']}_rep{rep}.json").write_text(json.dumps(trace, indent=2))

    status = "truncated" if meta.get("stop_reason") == "max_tokens" else "ok"
    append_jsonl(out_dir / "results.jsonl", {
        **key,
        "prompt": case["email"],
        "tags": [case["expected"], case.get("source", "unknown")],
        "expected": case["expected"],
        "answer": answer,
        **grade(case["expected"], answer),
        "status": status,
        "stop_reason": meta.get("stop_reason"),
        "model": served,
        "usage": meta.get("usage"),
        "latency_s": round(latency_s, 2),
        "retries": retries,
        "meta": {"total_cost_usd": meta.get("total_cost_usd")},
    })


def summarize(out_dir: Path) -> None:
    rows = [json.loads(line) for line in (out_dir / "results.jsonl").read_text().splitlines() if line.strip()]
    ok = [row for row in rows if row["status"] == "ok"]
    per_case = defaultdict(list)
    for row in ok:
        per_case[row["prompt_id"]].append(row["grade"]["accuracy"])
    case_means = [sum(v) / len(v) for v in per_case.values()]
    n = len(case_means)
    mean = sum(case_means) / n
    sd = math.sqrt(sum((m - mean) ** 2 for m in case_means) / (n - 1)) if n > 1 else 0.0
    half_width = 1.96 * sd / math.sqrt(n)

    recall = defaultdict(list)
    for row in ok:
        recall[row["expected"]].append(row["grade"]["accuracy"])
    format_ok = sum(row["grade"]["format_ok"] for row in ok) / len(ok)
    errors_path = out_dir / "errors.jsonl"
    n_errors = len(errors_path.read_text().splitlines()) if errors_path.exists() else 0
    truncated = len(rows) - len(ok)

    print("\nper-queue recall: " + ", ".join(f"{q} {sum(v) / len(v):.2f}" for q, v in sorted(recall.items())))
    print(f"format_ok: {format_ok:.2f}   errors: {n_errors}   truncated: {truncated}")
    print(f"accuracy: {mean:.2f} ± {half_width:.2f} (95% CI over {n} cases, {len(ok)} scored rows)")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="baseline")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--limit", type=int, help="only run the first N cases (pilot)")
    parser.add_argument("--approve-harness", action="store_true")
    args = parser.parse_args()

    check_harness(args.approve_harness)
    out_dir = FLOW_DIR / args.variant
    (out_dir / "traces").mkdir(parents=True, exist_ok=True)

    cases = json.loads((HERE / "cases.json").read_text())[: args.limit]
    done = done_keys(out_dir / "results.jsonl")
    todo = [(case, rep) for case in cases for rep in range(args.reps) if (case["id"], rep) not in done]
    print(f"{len(todo)} (case, rep) to run, {len(done)} already done")

    with ThreadPoolExecutor(WORKERS) as pool:
        futures = [pool.submit(run_case, case, rep, args.model, out_dir) for case, rep in todo]
        for future in futures:
            future.result()

    summarize(out_dir)


if __name__ == "__main__":
    main()
