"""Can a different model catch the claims qwen3:8b invented? Reviews, then scores."""

import json
import pathlib

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
MODELS = ["llama3.1:8b", "qwen2.5:14b"]
INSTRUCTION = (
    "You are reviewing a summary of a meeting transcript. Remove anything the "
    "transcript does not support. Return the corrected summary."
)


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


def review(model, transcript, summary):
    reply = httpx.post("http://localhost:11434/api/chat", json={
        "model": model,
        "messages": [
            {"role": "system", "content": INSTRUCTION},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\nSUMMARY:\n{summary}"},
        ],
        "stream": False, "think": False,
        "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 1200},
    }, timeout=600)
    reply.raise_for_status()
    return reply.json()["message"]["content"]


def still_there(document, claim):
    reply = httpx.post("http://localhost:11434/api/generate", json={
        "model": "bespoke-minicheck:7b",
        "prompt": f"Document: {document}\nClaim: {claim}",
        "stream": False,
        "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 2},
    }, timeout=600)
    reply.raise_for_status()
    return reply.json()["response"].strip().lower().startswith("yes")


rows = json.loads((RESULTS / "perclaim.json").read_text())
drafts = {}
for r in rows:
    drafts.setdefault(r["draft"], []).append(r)

path = RESULTS / "crossmodel.json"
store = json.loads(path.read_text()) if path.exists() else {}
for model in MODELS:
    for stem, claims in drafts.items():
        key = f"{model}|{stem}"
        if key in store:
            continue
        transcript = (ROOT / "transcripts" / f"{stem}.txt").read_text()
        store[key] = review(model, transcript, render(claims))
        path.write_text(json.dumps(store, indent=2))
        print(f"  {model} reviewed {stem}", flush=True)

print()
for model in MODELS:
    caught = fa = 0
    for r in rows:
        gone = not still_there(store[f"{model}|{r['draft']}"], r["text"])
        if r["truly_unsupported"]:
            caught += gone
        else:
            fa += gone
    print(f"{model:<16} caught {caught}/12 unsupported | removed {fa}/23 supported")
