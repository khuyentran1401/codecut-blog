"""Measure wall-clock cost of each reviewer approach over the same 9 drafts."""

import json
import pathlib
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
INSTRUCTION = (
    "You are reviewing a summary of a meeting transcript. Remove anything the "
    "transcript does not support. Return the corrected summary."
)
REWRITERS = ["qwen3:8b", "llama3.1:8b", "qwen2.5:14b", "qwen3:30b-a3b", "qwen3.8:27b-mlx"]
CHECKER = "bespoke-minicheck:7b"


def render(claims):
    out = []
    for section in ["decisions", "action_items", "risks"]:
        rs = [c for c in claims if c["section"] == section]
        if not rs:
            continue
        out.append(section.replace("_", " ").title())
        out += [f"- {c['text']}" for c in rs]
        out.append("")
    return "\n".join(out).strip()


def chat(model, transcript, summary):
    r = httpx.post("http://localhost:11434/api/chat", json={
        "model": model,
        "messages": [
            {"role": "system", "content": INSTRUCTION},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\nSUMMARY:\n{summary}"},
        ],
        "stream": False, "think": False,
        "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 1200},
    }, timeout=1800)
    r.raise_for_status()
    return r.json()


def judge(transcript, claim):
    r = httpx.post("http://localhost:11434/api/generate", json={
        "model": CHECKER,
        "prompt": f"Document: {transcript}\nClaim: {claim}",
        "stream": False,
        "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 2},
    }, timeout=600)
    r.raise_for_status()
    return r.json()


rows = json.loads((RESULTS / "perclaim.json").read_text())
drafts = {}
for r in rows:
    drafts.setdefault(r["draft"], []).append(r)
transcripts = {s: (ROOT / "transcripts" / f"{s}.txt").read_text() for s in drafts}

report = {}

# Rewriters: one call per draft (9 calls total).
for model in REWRITERS:
    chat(model, "warm up", "warm up")          # load weights, not measured
    total, calls = 0.0, 0
    for stem, claims in drafts.items():
        t0 = time.time()
        chat(model, transcripts[stem], render(claims))
        total += time.time() - t0
        calls += 1
    report[model] = {"calls": calls, "total_s": total, "per_call_s": total / calls}
    print(f"{model:<18} {calls:2} calls  {total:6.1f}s total  {total / calls:5.1f}s per call", flush=True)

# Checker: one call per claim (35 calls total).
judge("warm up", "warm up")
total, calls = 0.0, 0
for r in rows:
    t0 = time.time()
    judge(transcripts[r["draft"]], r["text"])
    total += time.time() - t0
    calls += 1
report[CHECKER] = {"calls": calls, "total_s": total, "per_call_s": total / calls}
print(f"{CHECKER:<18} {calls:2} calls  {total:6.1f}s total  {total / calls:5.1f}s per call", flush=True)

(RESULTS / "timing.json").write_text(json.dumps(report, indent=2))
print("\nwrote results/timing.json")
