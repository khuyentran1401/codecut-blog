"""Per-claim survival under each reviewer, measured the same way for all of them."""

import json
import pathlib

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

SELF = "qwen3:8b"
CHECKER = "bespoke-minicheck:7b"
# Reviewers that rewrite the summary, scored from their rewritten output.
REWRITERS = ["llama3.1:8b", "qwen2.5:14b", "qwen3.8:27b-mlx", "qwen3:30b-a3b"]


def still_there(document, claim):
    reply = httpx.post("http://localhost:11434/api/generate", json={
        "model": CHECKER,
        "prompt": f"Document: {document}\nClaim: {claim}",
        "stream": False,
        "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 2},
    }, timeout=600)
    reply.raise_for_status()
    return reply.json()["response"].strip().lower().startswith("yes")


rows = json.loads((RESULTS / "perclaim.json").read_text())
store = json.loads((RESULTS / "crossmodel.json").read_text())

out = []
for r in rows:
    row = {k: r[k] for k in ("draft", "id", "section", "text", "truly_unsupported")}
    # Keyed by the full model name: qwen3:8b and qwen3:30b-a3b would otherwise collide.
    row["removed"] = {
        SELF: not r["survives_free_rewrite"],
        CHECKER: not r["checker_supported"],
    }
    for model in REWRITERS:
        row["removed"][model] = not still_there(store[f"{model}|{r['draft']}"], r["text"])
    out.append(row)
(RESULTS / "reviewers.json").write_text(json.dumps(out, indent=2))

reviewers = [SELF, *REWRITERS, CHECKER]
unsupported = [r for r in out if r["truly_unsupported"]]
supported = [r for r in out if not r["truly_unsupported"]]

print(f"{'reviewer':<22}{'caught/12':<12}{'lost/23':<10}{'precision'}")
for model in reviewers:
    caught = sum(r["removed"][model] for r in unsupported)
    lost = sum(r["removed"][model] for r in supported)
    removals = caught + lost
    if removals:
        print(f"{model:<22}{caught:<12}{lost:<10}{caught}/{removals} = {caught / removals:.0%}")

general = [SELF, *REWRITERS]
missed = sum(1 for r in unsupported if not any(r["removed"][m] for m in general))
print(f"\nunsupported claims no general reviewer removed: {missed} of 12")
