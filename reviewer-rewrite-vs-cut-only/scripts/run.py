"""Three review versions over the same drafts: control, free rewrite, operations only."""

import json
import pathlib

import httpx

from schemas import SECTIONS, ReviewPlan

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = "qwen3:8b"

REVIEW_INSTRUCTION = (
    "You are reviewing a summary of a meeting transcript. "
    "Remove anything the transcript does not support."
)


def call(messages, schema=None, seed=0):
    body = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,
        "options": {"temperature": 0, "seed": seed, "num_ctx": 16384, "num_predict": 1200},
    }
    if schema is not None:
        body["format"] = schema.model_json_schema()
    reply = httpx.post("http://localhost:11434/api/chat", json=body, timeout=900)
    reply.raise_for_status()
    return reply.json()["message"]["content"]


def render(claims, with_ids):
    lines = []
    for section in SECTIONS:
        rows = [c for c in claims if c["section"] == section]
        if not rows:
            continue
        lines.append(section.replace("_", " ").title())
        for c in rows:
            prefix = f"[{c['id']}] " if with_ids else "- "
            lines.append(f"{prefix}{c['text']}")
        lines.append("")
    return "\n".join(lines).strip()


def free_rewrite(transcript, claims, seed):
    return call(
        [
            {"role": "system", "content": REVIEW_INSTRUCTION + " Return the corrected summary."},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\nSUMMARY:\n{render(claims, True)}"},
        ],
        seed=seed,
    )


def operations_only(transcript, claims, seed):
    ids = {c["id"] for c in claims}
    raw = call(
        [
            {"role": "system", "content": REVIEW_INSTRUCTION
             + " You may not write any text. Return only operations that refer to claim ids."},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\nSUMMARY:\n{render(claims, True)}"},
        ],
        schema=ReviewPlan,
        seed=seed,
    )
    plan = ReviewPlan.model_validate_json(raw)
    valid = [op for op in plan.operations
             if op.claim_id in ids or op.op == "drop_section"]
    rejected = len(plan.operations) - len(valid)
    kept = list(claims)
    for op in valid:
        if op.op in ("delete", "mark_unsupported"):
            kept = [c for c in kept if c["id"] != op.claim_id]
        elif op.op == "drop_section":
            kept = [c for c in kept if c["section"] != op.claim_id]
    return render(kept, False), [op.model_dump() for op in valid], rejected


def main(seed=0):
    for path in sorted((ROOT / "drafts").glob("*.json")):
        draft = json.loads(path.read_text())
        transcript = (ROOT / "transcripts" / draft["transcript"]).read_text()
        claims = draft["claims"]

        results = {"control": render(claims, False)}
        results["free_rewrite"] = free_rewrite(transcript, claims, seed)
        text, ops, rejected = operations_only(transcript, claims, seed)
        results["operations_only"] = text

        folder = ROOT / "outputs" / path.stem
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "operations_only.plan.json").write_text(
            json.dumps({"operations": ops, "rejected": rejected}, indent=2))
        for version, text in results.items():
            (folder / f"{version}.txt").write_text(text)
            print(f"\n{'=' * 72}\n{path.stem}  |  {version}\n{'=' * 72}\n{text}")
        print(f"\noperations returned: {json.dumps(ops)}   rejected ids: {rejected}")


if __name__ == "__main__":
    main()
