"""Natural-fabrication run: summarize, review two ways, score. No planted claims.

A claim is supported only if the transcript states it or a participant said it.
A risk counts as supported only if someone raised that risk. Consequences the
model worked out on its own are unsupported, however reasonable.
"""

import json
import pathlib
import sys

import httpx

from run import free_rewrite, operations_only
from schemas import SECTIONS, DraftSummary

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCORED_SECTIONS = [s for s in SECTIONS if s != "open_questions"]
SUMMARIZE = (
    "Summarize this council meeting transcript into four sections: "
    "decisions, action_items, risks, open_questions."
)


def ask_schema(schema, prompt, text, seed=0):
    reply = httpx.post(
        "http://localhost:11434/api/chat",
        json={
            "model": "qwen3:8b",
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": text},
            ],
            "format": schema.model_json_schema(),
            "stream": False,
            "think": False,
            "options": {"temperature": 0, "seed": seed, "num_ctx": 16384},
        },
        timeout=900,
    )
    reply.raise_for_status()
    return schema.model_validate_json(reply.json()["message"]["content"])


def supported(document, claim):
    reply = httpx.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "bespoke-minicheck:7b",
            "prompt": f"Document: {document}\nClaim: {claim}",
            "stream": False,
            "options": {"temperature": 0, "seed": 0, "num_ctx": 16384, "num_predict": 2},
        },
        timeout=900,
    )
    reply.raise_for_status()
    return reply.json()["response"].strip().lower().startswith("yes")


def review_all(folder):
    """Phase 1: every qwen call, so the model stays resident."""
    path = folder / "reviewed.json"
    drafts = json.loads(path.read_text()) if path.exists() else {}
    for path in sorted((folder / "transcripts").glob("*.txt")):
        if path.stem in drafts:
            continue
        transcript = path.read_text()
        summary = ask_schema(DraftSummary, SUMMARIZE, transcript)
        claims, n = [], 0
        for section in SECTIONS:
            for text in getattr(summary, section):
                n += 1
                claims.append({"id": str(n), "section": section, "text": text})
        drafts[path.stem] = {
            "claims": claims,
            "free_rewrite": free_rewrite(transcript, claims, 0),
            "operations_only": operations_only(transcript, claims, 0)[0],
        }
        (folder / "reviewed.json").write_text(json.dumps(drafts, indent=2))
        print(f"  reviewed {path.stem}: {len(claims)} claims")
    return drafts


def score_all(folder, drafts):
    """Phase 2: every checker call, so that model stays resident."""
    rows = []
    for stem, d in drafts.items():
        transcript = (folder / "transcripts" / f"{stem}.txt").read_text()
        for claim in d["claims"]:
            row = dict(claim, draft=stem, checker_supported=supported(transcript, claim["text"]))
            for version in ("free_rewrite", "operations_only"):
                row[f"survives_{version}"] = supported(d[version], claim["text"])
            rows.append(row)
        print(f"  scored {stem}")
    (folder / "claims.json").write_text(json.dumps(rows, indent=2))
    return rows


def main(batch):
    folder = ROOT / batch
    (folder / "outputs").mkdir(exist_ok=True)
    drafts = review_all(folder)
    for stem, d in drafts.items():
        for version in ("free_rewrite", "operations_only"):
            (folder / "outputs" / f"{stem}__{version}.txt").write_text(d[version])
    rows = score_all(folder, drafts)
    print(f"\n{'draft':<7}{'id':<4}{'section':<14}{'checker':<8}{'free':<7}{'ops':<7}claim")
    for r in rows:
        scored = r["section"] in SCORED_SECTIONS
        print(f"{r['draft']:<7}{r['id']:<4}{r['section']:<14}"
              f"{('sup' if r['checker_supported'] else 'UNSUP'):<8}"
              f"{('kept' if r['survives_free_rewrite'] else 'gone'):<7}"
              f"{('kept' if r['survives_operations_only'] else 'gone'):<7}"
              f"{'' if scored else '(unscored) '}{r['text'][:68]}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "natural")
