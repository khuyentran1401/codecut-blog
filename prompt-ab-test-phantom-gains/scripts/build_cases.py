"""Extract the pilot case set from BFCL V4 and write cases.jsonl.

BFCL's own `BFCL_v4_format_sensitivity.json` names the entries it considers
representative of the full benchmark. We take the single-call categories from
that selection: `simple_python` (one function offered) and `multiple` (2-4
functions offered, model must pick). Parallel categories expect more than one
call and are excluded.
"""

import json
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/ShishirPatil/gorilla/main/berkeley-function-call-leaderboard/bfcl_eval/data"
ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = {"live_multiple": 86, "multiple": 14}  # harder than simple/multiple: median 4 candidate functions

# BFCL parameter types -> JSON Schema types the OpenAI tools format accepts.
TYPE_MAP = {
    "dict": "object",
    "float": "number",
    "integer": "integer",
    "string": "string",
    "boolean": "boolean",
    "array": "array",
    "tuple": "array",
    "any": "string",
}


def fetch_jsonl(url):
    text = urllib.request.urlopen(url).read().decode()
    return {
        json.loads(line)["id"]: json.loads(line)
        for line in text.splitlines()
        if line.strip()
    }


def to_json_schema(node):
    """Rewrite one BFCL parameter node into JSON Schema, recursively."""
    out = dict(node)
    out["type"] = TYPE_MAP.get(node.get("type", "string"), "string")
    if "properties" in out:
        out["properties"] = {k: to_json_schema(v) for k, v in out["properties"].items()}
    if "items" in out and isinstance(out["items"], dict):
        out["items"] = to_json_schema(out["items"])
    return out


def to_openai_tool(fn):
    params = to_json_schema(fn["parameters"])
    params.setdefault("required", [])
    return {
        "type": "function",
        "function": {
            "name": fn["name"],
            "description": fn.get("description", ""),
            "parameters": params,
        },
    }


def main():
    selection = json.load(
        urllib.request.urlopen(f"{RAW}/BFCL_v4_format_sensitivity.json")
    )

    cases = []
    for category, count in CATEGORIES.items():
        questions = fetch_jsonl(f"{RAW}/BFCL_v4_{category}.json")
        answers = fetch_jsonl(f"{RAW}/possible_answer/BFCL_v4_{category}.json")
        for case_id in selection[category][:count]:
            case = questions[case_id]
            # Live entries can carry a system message ahead of the user turn.
            cases.append(
                {
                    "id": case_id,
                    "category": category,
                    "messages": case["question"][0],
                    "tools": [to_openai_tool(f) for f in case["function"]],
                    "ground_truth": answers[case_id]["ground_truth"],
                }
            )

    path = ROOT / "cases.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in cases))
    print(f"wrote {len(cases)} cases to {path}")
    for c in cases:
        last = c["messages"][-1]["content"].replace("\n", " ")
        print(f"  {c['id']:24} {len(c['tools']):2d} tool(s)  {last[:54]}")


if __name__ == "__main__":
    main()
