"""Per-claim survival under each reviewer, measured the same way for all of them."""

import json
import pathlib

import httpx

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


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
store = json.loads((RESULTS / "crossmodel.json").read_text())
out = []
for r in rows:
    row = {k: r[k] for k in ("draft", "id", "section", "text", "truly_unsupported")}
    row["removed_self"] = not r["survives_free_rewrite"]
    row["flagged_checker"] = not r["checker_supported"]
    for model in ("llama3.1:8b", "qwen2.5:14b"):
        row[f"removed_{model.split(':')[0]}"] = not still_there(
            store[f"{model}|{r['draft']}"], r["text"])
    out.append(row)
(RESULTS / "reviewers.json").write_text(json.dumps(out, indent=2))

cols = ["removed_self", "removed_llama3.1", "removed_qwen2.5", "flagged_checker"]
u = [r for r in out if r["truly_unsupported"]]
s = [r for r in out if not r["truly_unsupported"]]
print(f"{'reviewer':<18}{'caught/12':<12}{'lost/23':<10}{'precision'}")
for c in cols:
    caught = sum(r[c] for r in u); lost = sum(r[c] for r in s)
    tot = caught + lost
    print(f"{c.split('_')[1]:<18}{caught:<12}{lost:<10}{caught}/{tot} = {caught/tot:.0%}" if tot else "")
print(f"\nunsupported claims no reviewer removed: "
      f"{sum(1 for r in u if not any(r[c] for c in cols[:3]))} of 12")
