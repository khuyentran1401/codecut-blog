"""Run the thinking-mode benchmark used in the article."""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

MODEL = "qwen3:30b-a3b"
URL = "http://localhost:11434/api/chat"
SYSTEM = (
    "You are a careful financial assistant. Answer the question with a "
    "single number only. Do not include currency symbols, thousands "
    "separators, units, or any explanation in the answer field."
)
SCHEMA = {
    "type": "object",
    "required": ["answer"],
    "properties": {"answer": {"type": "number"}},
}
GREEDY = {"temperature": 0}
THINKING = {"temperature": 0.6, "top_p": 0.95, "top_k": 20, "min_p": 0.0}
ANSWER_TOLERANCE = 0.005


class Mode(Enum):
    PLAIN = "plain"
    THINKING = "thinking"


@dataclass(frozen=True)
class Problem:
    name: str
    kind: str
    prompt: str
    expected: float


@dataclass(frozen=True)
class RunResult:
    problem: Problem
    mode: Mode
    answer: float
    seconds: float
    correct: bool


PROBLEMS = [
    Problem(
        "fifo-leftover",
        "multi",
        """A deposit of $5,000.00 funds these charges, in order:
  1. $1,200.00
  2. $2,000.00
  3. $2,400.00
A charge is only paid if the full amount is still available;
otherwise it is skipped and the next one is considered.
How many dollars are left unspent? Answer to 2 decimal places.""",
        1800.00,
    ),
    Problem(
        "split-discrepancy",
        "multi",
        """A parent transaction of $1,000.00 was split into these children:
  8.84, 86.18, 74.53, 74.53, 20.64, 12.61, 1.49, 1.49, 719.59
What is the difference between the parent amount and the total of the children?
Answer the absolute difference, to 2 decimal places.""",
        0.10,
    ),
    Problem(
        "installment-fees",
        "multi",
        """An invoice of $4,800.00 was paid in 3 equal installments.
Each installment was charged a 2.5% processing fee.
What were the total processing fees, to 2 decimal places?""",
        120.00,
    ),
    Problem(
        "unspent-after-refund",
        "multi",
        """A deposit of $26,000.00 funded charges of $5,000.00 and $3,500.00.
A refund of $1,200.00 was then credited back against the second charge.
How many dollars of the deposit remain unspent? Answer to 2 decimal places.""",
        18700.00,
    ),
    Problem(
        "which-deposit",
        "multi",
        """Two deposits arrived:
  A on 1 July, $10,000.00
  B on 15 July, $4,000.00
Spending, in order, always drawn from the oldest money still available:
  1 July: $6,000.00
  20 July: $6,500.00
How many dollars of the 20 July charge come from deposit B?
Answer to 2 decimal places.""",
        2500.00,
    ),
    Problem(
        "fifo-count",
        "multi",
        """A deposit of $8,000.00 funds these charges, in order:
  1. $2,500.00
  2. $3,000.00
  3. $2,800.00
  4. $1,500.00
A charge is only paid if the full amount is still available;
otherwise it is skipped and the next one is considered.
How many charges are paid in full?""",
        3,
    ),
    Problem(
        "split-balanced",
        "multi",
        """A parent transaction of $250.00 was split into these children:
  100.00, 60.50, 39.50, 50.00
What is the difference between the parent amount and the total of the children?
Answer the absolute difference, to 2 decimal places.""",
        0.00,
    ),
    Problem(
        "fee-share",
        "multi",
        """A deposit of $1,000.00 carried an $8.84 fee.
The deposit funded exactly 4 purchases of equal size.
If the fee is divided equally between those 4 purchases,
how many dollars of the FEE does each purchase carry?
Answer to 2 decimal places.""",
        2.21,
    ),
    Problem(
        "unit-price",
        "single",
        """An order totalling $148.50 contained 27 identical items.
What did each item cost, to 2 decimal places?""",
        5.50,
    ),
    Problem(
        "percent-of-deposit",
        "single",
        """A deposit of $1,250.00 funded a single charge of $100.00.
What percentage of the deposit was that charge?
Answer to 2 decimal places.""",
        8.00,
    ),
    Problem(
        "duplicates-count",
        "single",
        """These are card transactions from one account:
  1. UBER TRIP HOUSTON $18.50
  2. STARBUCKS STORE 221 $6.75
  3. UBER *TRIP - HOUSTON $18.50
  4. STARBUCKS #0221 SEATTLE $6.75
  5. CHIPOTLE 2841 $12.40
Two rows are the same purchase if they are the same merchant and the
same amount, however differently the merchant is written.
How many duplicate pairs are there?""",
        2,
    ),
    Problem(
        "duplicates-none",
        "single",
        """These are card transactions from one account:
  1. UBER TRIP HOUSTON $18.50
  2. UBER TRIP HOUSTON $22.10
  3. STARBUCKS STORE 221 $6.75
  4. STARBUCKS #0221 SEATTLE $7.25
Two rows are the same purchase if they are the same merchant and the
same amount, however differently the merchant is written.
How many duplicate pairs are there?""",
        0,
    ),
]


def get_ollama_message(problem: Problem, mode: Mode, seed: int) -> dict:
    options = dict(THINKING if mode is Mode.THINKING else GREEDY, seed=seed)
    body = {
        "model": MODEL,
        "stream": False,
        "think": mode is Mode.THINKING,
        "format": SCHEMA,
        "options": options,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": problem.prompt},
        ],
    }
    request = urllib.request.Request(
        URL, json.dumps(body).encode(), {"Content-Type": "application/json"}
    )
    reply = json.loads(urllib.request.urlopen(request).read())
    return reply["message"]


def extract_answer(message: dict) -> float:
    return float(json.loads(message["content"])["answer"])


def preview_thinking(message: dict, max_lines: int) -> str:
    if max_lines == 0 or not message.get("thinking"):
        return ""

    lines = [line for line in message["thinking"].splitlines() if line.strip()]
    if len(lines) <= max_lines:
        return "\n".join(lines)

    head_count = max_lines // 2
    tail_count = max_lines - head_count
    return "\n".join(lines[:head_count] + ["..."] + lines[-tail_count:])


def is_correct(answer: float, expected: float) -> bool:
    return abs(answer - expected) <= ANSWER_TOLERANCE


def run_problem(problem: Problem, mode: Mode, seed: int) -> RunResult:
    start = time.perf_counter()
    message = get_ollama_message(problem, mode, seed)
    seconds = time.perf_counter() - start
    answer = extract_answer(message)
    return RunResult(problem, mode, answer, seconds, is_correct(answer, problem.expected))


def run_all(seed: int) -> list[RunResult]:
    return [
        run_problem(problem, mode, seed)
        for problem in PROBLEMS
        for mode in (Mode.PLAIN, Mode.THINKING)
    ]


def average_time(results: Iterable[RunResult], mode: Mode, kind: str) -> float:
    matching = [
        result.seconds
        for result in results
        if result.mode is mode and result.problem.kind == kind
    ]
    return sum(matching) / len(matching)


def count_correct(results: Iterable[RunResult], mode: Mode, kind: str) -> tuple[int, int]:
    matching = [
        result
        for result in results
        if result.mode is mode and result.problem.kind == kind
    ]
    return sum(result.correct for result in matching), len(matching)


def print_summary(results: list[RunResult]) -> None:
    print("| Kind | Plain | Thinking | Average Time |")
    print("| --- | ---: | ---: | ---: |")
    for kind in ("multi", "single"):
        plain_correct, total = count_correct(results, Mode.PLAIN, kind)
        thinking_correct, _ = count_correct(results, Mode.THINKING, kind)
        plain_time = average_time(results, Mode.PLAIN, kind)
        thinking_time = average_time(results, Mode.THINKING, kind)
        label = "Multi-step" if kind == "multi" else "Single-step"
        print(
            f"| {label} ({total} problems) | "
            f"{plain_correct} / {total} | "
            f"{thinking_correct} / {total} | "
            f"{plain_time:.2f}s -> {thinking_time:.2f}s |"
        )


def print_details(results: list[RunResult]) -> None:
    print("\n| Problem | Kind | Mode | Expected | Answer | Time | Correct |")
    print("| --- | --- | --- | ---: | ---: | ---: | --- |")
    for result in results:
        mark = "yes" if result.correct else "no"
        print(
            f"| {result.problem.name} | {result.problem.kind} | "
            f"{result.mode.value} | {result.problem.expected:.2f} | "
            f"{result.answer:.2f} | {result.seconds:.2f}s | {mark} |"
        )


def show_trace(problem_name: str, seed: int, max_lines: int) -> None:
    problem = next(problem for problem in PROBLEMS if problem.name == problem_name)
    message = get_ollama_message(problem, Mode.THINKING, seed)
    trace = preview_thinking(message, max_lines)
    if trace:
        print(trace)
    print(extract_answer(message))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local LLM thinking-mode benchmark."
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument(
        "--trace",
        choices=[problem.name for problem in PROBLEMS],
        help="Print a thinking preview for one problem instead of running all.",
    )
    parser.add_argument("--trace-lines", type=int, default=4)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.trace:
        show_trace(args.trace, args.seed, args.trace_lines)
        return

    results = run_all(args.seed)
    print_summary(results)
    print_details(results)


if __name__ == "__main__":
    main()
