"""Score a tool call against BFCL ground truth.

Reimplements BFCL's simple-AST check for single-call categories. BFCL wraps
acceptable values in a list at every level of nesting, so the matcher has to
recurse: `{"update_info": [{"name": ["John Doe"]}]}` means update_info must be a
dict whose `name` is one of ["John Doe"], not a dict equal to {"name": [...]}.

An omitted parameter is allowed only when "" is among its acceptable values.
Extra arguments the ground truth does not list count as wrong, as in BFCL.
"""

import json
import re

# BFCL's own normalizer: strip spaces and ",./-_*^", lowercase, single to double
# quotes. It exists so "April 1, 2024" and "April 1 2024" compare equal, and it
# also makes "Ha Noi" and "Hanoi" the same string.
_PUNCTUATION = r"[ \,\.\/\-\_\*\^]"


def normalize(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return re.sub(_PUNCTUATION, "", value).lower().replace("'", '"')
    if isinstance(value, (int, float)):
        return float(value)
    return value


def matches_option(actual, option):
    """Does `actual` match one acceptable value? `option` may nest further."""
    if isinstance(option, dict):
        if not isinstance(actual, dict):
            return False
        if set(actual) - set(option):
            return False
        for key, allowed in option.items():
            if key not in actual:
                if not (isinstance(allowed, list) and "" in allowed):
                    return False
            elif not matches_any(actual[key], allowed):
                return False
        return True

    if isinstance(option, list):
        if not isinstance(actual, list) or len(actual) != len(option):
            return False
        return all(matches_option(a, o) for a, o in zip(actual, option))

    return normalize(actual) == normalize(option)


def matches_any(actual, allowed):
    """`allowed` is BFCL's list of acceptable values for one parameter."""
    if not isinstance(allowed, list):
        return matches_option(actual, allowed)
    return any(matches_option(actual, option) for option in allowed)


def is_correct(call, ground_truth):
    """call is {"name": str, "arguments": dict} or None. Returns (ok, reason)."""
    if call is None:
        return False, "no tool call"

    expected = ground_truth[0]
    expected_name = next(iter(expected))
    if call["name"] != expected_name:
        return False, f"wrong function: {call['name']} != {expected_name}"

    expected_args = expected[expected_name]
    actual_args = call["arguments"]

    for extra in sorted(set(actual_args) - set(expected_args)):
        return False, f"unexpected argument: {extra}"

    for param, allowed in expected_args.items():
        if param not in actual_args:
            if "" not in allowed:
                return False, f"missing required argument: {param}"
            continue
        if not matches_any(actual_args[param], allowed):
            return False, f"{param}={json.dumps(actual_args[param])} not acceptable"

    return True, "ok"


if __name__ == "__main__":
    import sys
    from collections import defaultdict
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    cases = {
        json.loads(l)["id"]: json.loads(l)
        for l in (root / "cases.jsonl").read_text().splitlines()
        if l.strip()
    }
    path = root / (sys.argv[1] if len(sys.argv) > 1 else "results.jsonl")
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]

    scores = defaultdict(lambda: [0, 0])
    for row in rows:
        ok, reason = is_correct(row.get("call"), cases[row["case_id"]]["ground_truth"])
        row["correct"], row["reason"] = ok, reason
        key = (row["condition"], row["prompt"], row["provider_requested"] or "UNPINNED", row["repeat"])
        scores[key][0] += ok
        scores[key][1] += 1

    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    for key in sorted(scores):
        good, total = scores[key]
        print(f"{key[0]:9} prompt {key[1]} rep{key[3]}  {key[2]:22} {good}/{total}")
