"""Sweep how many earlier assistant turns show a body, and measure whether the
model's next commit message has one.

The skill file is A4_agree in every run: its rule says one line and all four of
its examples show one line. Only the conversation changes.

Two history kinds at each turn count:
  conflict - the assistant's earlier turns carry a body
  clean    - the same text, with the body moved into the user turn

Usage: uv run scripts/run_sweep.py --runs 5
"""

import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

from induction import INDUCTION

ROOT = Path(__file__).resolve().parent.parent
FRONTMATTER = re.compile(r"^---\n.*?\n---\n", re.S)
TURN_COUNTS = [0, 2, 4, 6, 8, 10, 15, 20]
CLEAN_AT = TURN_COUNTS
CORRECTED_AT = TURN_COUNTS


def skill_body(name="commit-message"):
    text = (ROOT / "skills" / name / "SKILL.md").read_text()
    return FRONTMATTER.sub("", text).strip()


def history(turns, kind):
    messages = []
    for task, reply in INDUCTION[:turns]:
        subject, _, body = reply.partition("\n\n")
        if kind == "conflict":
            messages += [{"role": "user", "content": task},
                         {"role": "assistant", "content": reply}]
        elif kind == "corrected":
            # the bad answer stays in the history, followed by a correction
            # from the user and the agent's own fixed answer
            messages += [{"role": "user", "content": task},
                         {"role": "assistant", "content": reply},
                         {"role": "user", "content": "one line only, no body"},
                         {"role": "assistant", "content": subject}]
        else:
            flat = body.replace("\n", " ")
            messages += [{"role": "user", "content": f"{task}. {flat}"},
                         {"role": "assistant", "content": subject}]
    return messages


def ask(model, messages):
    payload = {"model": model, "messages": messages, "stream": False,
               "think": False, "options": {"temperature": 0}}
    request = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.load(response)["message"]["content"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--out", default="results-session.jsonl")
    parser.add_argument("--cases", default="cases.jsonl")
    parser.add_argument("--resume", action="store_true",
                        help="append to --out, skipping (turns, kind) cells it already holds")
    args = parser.parse_args()

    system = skill_body()
    cases = [json.loads(line) for line in (ROOT / args.cases).read_text().splitlines() if line]
    out_path = ROOT / args.out
    done_cells = set()
    if args.resume and out_path.exists():
        done_cells = {(json.loads(line)["turns"], json.loads(line)["kind"])
                      for line in out_path.read_text().splitlines() if line}
    out = out_path.open("a" if args.resume else "w")

    plan = ([(t, "conflict") for t in TURN_COUNTS]
            + [(t, "clean") for t in CLEAN_AT]
            + [(t, "corrected") for t in CORRECTED_AT])
    plan = [cell for cell in plan if cell not in done_cells]
    total = len(plan) * len(cases) * args.runs
    done = 0

    for turns, kind in plan:
        past = history(turns, kind)
        chars = sum(len(m["content"]) for m in past)
        for case in cases:
            for run in range(args.runs):
                messages = ([{"role": "system", "content": system}] + past
                            + [{"role": "user", "content": case["task"]}])
                started = time.time()
                reply = ask(args.model, messages)
                out.write(json.dumps({
                    "model": args.model, "turns": turns, "kind": kind,
                    "case": case["id"], "task": case["task"], "run": run,
                    "history_chars": chars,
                    "seconds": round(time.time() - started, 1),
                    "output": reply,
                }) + "\n")
                out.flush()
                done += 1
        print(f"turns={turns:<3} {kind:9} done  ({done}/{total})", flush=True)
    out.close()


if __name__ == "__main__":
    main()
