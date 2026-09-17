"""Issue the pilot requests and record who served each one.

Modes:
  sweep    prompt A, pinned to each provider in turn        (provider spread)
  pinned   prompt B, pinned to one provider                 (prompt effect)
"""

import argparse
import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
MODEL = "deepseek/deepseek-v4-flash-0731"

# Six of the 28 tool-capable endpoints, spanning declared precision and price.
PROVIDERS = [
    "open-inference/fp8",
    "deepinfra/fp8",
    "relace/fp4",
    "digitalocean",
    "together",
    "wafer/fast",
]
# coreweave/fp8 is excluded: it rejects any function name containing a dot with a
# 400, which most live BFCL cases use. Recorded as its own finding, not scored.
PIN = "deepinfra/fp8"

SYSTEM_A = "You are a helpful assistant with access to tools. Call the appropriate function."
SYSTEM_B = SYSTEM_A + " If a parameter is not specified in the request, omit it rather than guessing a value."
SYSTEMS = {"A": SYSTEM_A, "B": SYSTEM_B}


def load_key():
    for line in (ROOT.parent.parent / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("OPENROUTER_API_KEY not found in .env")


client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=load_key())


def ask(case, prompt, provider, condition, repeat=0):
    body = {}
    if provider:
        # allow_fallbacks False is what makes `only` a pin rather than a preference.
        body["provider"] = {"only": [provider], "allow_fallbacks": False}

    row = {
        "case_id": case["id"],
        "category": case["category"],
        "prompt": prompt,
        "condition": condition,
        "repeat": repeat,
        "provider_requested": provider,
        "ts": time.time(),
    }

    started = time.time()
    try:
        reply = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEMS[prompt]}, *case["messages"]],
            tools=case["tools"],
            temperature=0,
            top_p=1,
            max_tokens=1024,
            extra_body=body,
        )
    except Exception as exc:
        row.update(error=f"{type(exc).__name__}: {exc}"[:400], call=None)
        return row

    raw = reply.model_dump()
    row["latency_ms"] = round((time.time() - started) * 1000)
    row["provider_served"] = raw.get("provider")
    row["response_id"] = reply.id
    row["finish_reason"] = reply.choices[0].finish_reason
    message = reply.choices[0].message

    call = None
    if message.tool_calls:
        fn = message.tool_calls[0].function
        try:
            call = {"name": fn.name, "arguments": json.loads(fn.arguments or "{}")}
        except json.JSONDecodeError:
            row["bad_arguments"] = fn.arguments
    row["call"] = call
    row["content"] = message.content
    provider_slug = provider.replace("/", "-") if provider else "no-provider"
    (ROOT / "transcripts" / f"{case['id']}_{prompt}_{provider_slug}_{repeat}.json").write_text(
        json.dumps(raw, indent=2)
    )
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["sweep", "pinned"])
    parser.add_argument("--repeat", type=int, default=0)
    parser.add_argument("--out", default="results.jsonl")
    args = parser.parse_args()

    cases = [json.loads(l) for l in (ROOT / "cases.jsonl").read_text().splitlines() if l.strip()]

    jobs = []
    if args.mode == "sweep":
        # Interleaved, not blocked: a slow hour cannot land on one provider.
        for case in cases:
            for provider in PROVIDERS:
                jobs.append((case, "A", provider, "sweep", args.repeat))
        random.shuffle(jobs)
    elif args.mode == "pinned":
        jobs = [(case, "B", PIN, "pinned", args.repeat) for case in cases]

    print(f"{args.mode}: {len(jobs)} requests")
    with ThreadPoolExecutor(6) as pool:
        rows = list(pool.map(lambda j: ask(*j), jobs))

    with (ROOT / args.out).open("a") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    errors = [r for r in rows if r.get("error")]
    print(f"done. {len(rows) - len(errors)} ok, {len(errors)} errors")
    for row in errors[:5]:
        print(f"  {row['provider_requested']}: {row['error'][:120]}")


if __name__ == "__main__":
    main()
