"""The reviewer call and the summary renderer, shared by the other scripts."""

import httpx

from schemas import SECTIONS

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


def render(claims):
    lines = []
    for section in SECTIONS:
        rows = [c for c in claims if c["section"] == section]
        if not rows:
            continue
        lines.append(section.replace("_", " ").title())
        for c in rows:
            prefix = f"[{c['id']}] "
            lines.append(f"{prefix}{c['text']}")
        lines.append("")
    return "\n".join(lines).strip()


def free_rewrite(transcript, claims, seed):
    return call(
        [
            {"role": "system", "content": REVIEW_INSTRUCTION + " Return the corrected summary."},
            {"role": "user", "content": f"TRANSCRIPT:\n{transcript}\n\nSUMMARY:\n{render(claims)}"},
        ],
        seed=seed,
    )

