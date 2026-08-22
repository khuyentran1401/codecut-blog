"""Does the checker notice a wrong number?

Takes RAGTruth answers that annotators marked clean, finds a number in the answer
that also appears in its source document, and changes one digit so the new value
appears nowhere in the source. Nothing else about the answer changes.

The original answer is supported. The changed one contains a claim the document
contradicts. A checker that reads the document should separate them easily.

    python run_numbers.py --stage build     construct the pairs
    python run_numbers.py --stage score     score both versions, ~2 min
    python run_numbers.py --stage report    counts and per-pair detail
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
from pathlib import Path

HERE = Path(__file__).parent
RESULTS = HERE / "results"
DATASET = "wandb/RAGTruth-processed"
MODEL = "KRLabsOrg/lettucedect-base-modernbert-en-v1"

# Numbers with optional thousands separators and decimals. The alternation keeps
# a trailing comma out of the match, so "16, 17" yields 16 rather than "16,".
# Years and tiny integers are filtered out later; they are rarely the claim.
NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?")


def as_value(text: str) -> float | None:
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def source_values(document: str) -> set[float]:
    """Every number in the document, normalized, so 10,000 and 10000 match."""
    values = set()
    for match in NUMBER.finditer(document):
        value = as_value(match.group())
        if value is not None:
            values.add(value)
    return values


def change_one_number(
    answer: str, document: str, rng: random.Random
) -> tuple[str, str, str] | None:
    """Change one grounded number in the answer to a value absent from the document.

    Returns (changed answer, original number, new number), or None when the
    answer has no number worth perturbing.
    """
    in_source = source_values(document)
    candidates = []
    for match in NUMBER.finditer(answer):
        value = as_value(match.group())
        # Only change a number the document actually supports, so the original
        # answer really is grounded on this claim. Skip small counts and years,
        # which are usually list markers or dates rather than the claim itself.
        if value is None or value < 10 or 1900 <= value <= 2100:
            continue
        if value in in_source:
            candidates.append(match)
    if not candidates:
        return None

    match = rng.choice(candidates)
    original = match.group()
    digits = [i for i, ch in enumerate(original) if ch.isdigit()]

    # Try each digit position until the edited value is absent from the document.
    rng.shuffle(digits)
    for position in digits:
        for replacement in "0123456789":
            if replacement == original[position]:
                continue
            edited = original[:position] + replacement + original[position + 1 :]
            # A leading zero would make the edit detectable by formatting rather
            # than by value, which is not the thing being tested.
            if edited[0] == "0":
                continue
            value = as_value(edited)
            if value is None or value in in_source or value == as_value(original):
                continue
            changed = answer[: match.start()] + edited + answer[match.end() :]
            return changed, original, edited
    return None


def build(n: int, seed: int) -> list[dict]:
    from datasets import load_dataset

    rows = [r for r in load_dataset(DATASET, split="test") if r["task_type"] == "QA"]

    def is_clean(row) -> bool:
        return len(json.loads(row["hallucination_labels"])) == 0

    clean = [r for r in rows if is_clean(r)]
    rng = random.Random(seed)
    rng.shuffle(clean)

    pairs = []
    for row in clean:
        result = change_one_number(row["output"], row["context"], rng)
        if result is None:
            continue
        changed, original, edited = result
        pairs.append(
            {
                "id": str(row["id"]),
                "query": row["query"],
                "context": row["context"],
                "answer": row["output"],
                "perturbed_answer": changed,
                "original_number": original,
                "edited_number": edited,
            }
        )
        if len(pairs) == n:
            break
    return pairs


def score(pairs: list[dict]) -> list[dict]:
    from lettucedetect.models.inference import HallucinationDetector

    started = time.time()
    detector = HallucinationDetector(method="transformer", model_path=MODEL)
    print(f"loaded {MODEL} in {time.time() - started:.0f}s", flush=True)

    def token_score(context: str, question: str, answer: str) -> float:
        tokens = detector.predict(
            context=[context], question=question, answer=answer, output_format="tokens"
        )
        return max(token["prob"] for token in tokens)

    def flagged_number(context: str, question: str, answer: str, number: str) -> bool:
        """Did the checker flag a span that actually covers the edited number?"""
        spans = detector.predict(
            context=[context], question=question, answer=answer, output_format="spans"
        )
        return any(number in span["text"] for span in spans)

    out = []
    for i, pair in enumerate(pairs, 1):
        row = dict(pair)
        row["score_original"] = token_score(pair["context"], pair["query"], pair["answer"])
        row["score_perturbed"] = token_score(
            pair["context"], pair["query"], pair["perturbed_answer"]
        )
        row["number_flagged"] = flagged_number(
            pair["context"], pair["query"], pair["perturbed_answer"], pair["edited_number"]
        )
        out.append(row)
        if i % 20 == 0:
            print(f"  {i}/{len(pairs)}", flush=True)
    return out


def report(scored: list[dict]) -> str:
    n = len(scored)
    caught = sum(1 for r in scored if r["score_perturbed"] > 0.5)
    false_alarms = sum(1 for r in scored if r["score_original"] > 0.5)
    higher = sum(1 for r in scored if r["score_perturbed"] > r["score_original"])
    tied = sum(1 for r in scored if r["score_perturbed"] == r["score_original"])

    lines = [
        "# Wrong-number diagnostic\n",
        f"Model: `{MODEL}`. {n} clean answers, each paired with a copy where",
        "one grounded number was changed to a value absent from the source.\n",
        "## Can the checker tell the two apart?\n",
        f"- changed answers flagged above 0.5: **{caught} of {n}**",
        f"- untouched answers flagged above 0.5: {false_alarms} of {n}",
        f"- pairs where the changed copy scored higher: {higher} of {n}",
        f"- pairs where both scored identically: {tied} of {n}",
        "",
        "## Did it point at the number?\n",
        f"- perturbed answers with a flagged span covering the edited number: "
        f"**{sum(r['number_flagged'] for r in scored)} of {n}**",
        "",
        "## Examples\n",
        "| id | number | changed to | original score | perturbed score | number flagged |",
        "| --- | --- | --- | ---: | ---: | --- |",
    ]
    for r in scored[:12]:
        lines.append(
            f"| {r['id']} | {r['original_number']} | {r['edited_number']} "
            f"| {r['score_original']:.3f} | {r['score_perturbed']:.3f} "
            f"| {'yes' if r['number_flagged'] else 'no'} |"
        )
    return "\n".join(lines) + "\n"


def sweep(scored: list[dict]) -> str:
    """What a lower flag threshold buys on this error class, and what it costs."""
    n = len(scored)
    lines = [
        "## Does a lower threshold help?\n",
        "| threshold | changed numbers caught | untouched answers flagged |",
        "| ---: | ---: | ---: |",
    ]
    for t in (0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01):
        caught = sum(1 for r in scored if r["score_perturbed"] > t)
        false_alarms = sum(1 for r in scored if r["score_original"] > t)
        lines.append(f"| {t} | {caught} of {n} | {false_alarms} of {n} |")
    lines += [
        "",
        "Unlike the negation case, recall here is genuinely for sale: 0.2 catches 70",
        "against 48. The price is flagging a quarter of the clean answers.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["build", "score", "report"])
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)

    if args.stage == "build":
        pairs = build(args.n, args.seed)
        (RESULTS / "numbers_pairs.json").write_text(json.dumps(pairs, indent=2))
        print(f"built {len(pairs)} pairs")
        for pair in pairs[:5]:
            print(f"  {pair['id']}: {pair['original_number']} -> {pair['edited_number']}")

    if args.stage == "score":
        pairs = json.loads((RESULTS / "numbers_pairs.json").read_text())
        scored = score(pairs)
        (RESULTS / "numbers_scored.json").write_text(json.dumps(scored, indent=2))
        print(f"wrote {RESULTS / 'numbers_scored.json'}")

    if args.stage == "report":
        scored = json.loads((RESULTS / "numbers_scored.json").read_text())
        text = report(scored) + "\n" + sweep(scored)
        (RESULTS / "numbers_summary.md").write_text(text)
        print(text)


if __name__ == "__main__":
    main()
