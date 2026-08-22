"""Does the checker catch a flipped negation?

A negation flip is the smallest claim-changing edit available. Adding "not" to a
sentence inverts its meaning completely while touching about four characters, so
it separates how *wrong* a claim is from how much *text* it occupies.

Each answer here is one annotators marked clean. The edit inserts a negation into
a sentence the source supports, producing a claim the source contradicts:

    supported     Foods that contain gluten include wheat
    negated       Foods that do not contain gluten include wheat

Only sentences whose negated form is absent from the source are used, and the
original sentence must be present in substance, so the flip really does create an
unsupported claim rather than restating something the document already denies.

    python run_negation.py --stage build
    python run_negation.py --stage score
    python run_negation.py --stage report
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

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# Each pattern turns an affirmative verb phrase into its negation. Ordered so the
# more specific auxiliaries are tried before the bare copulas.
FLIPS = [
    (re.compile(r"\b(can)\b", re.IGNORECASE), "cannot"),
    (re.compile(r"\b(will)\b", re.IGNORECASE), "will not"),
    (re.compile(r"\b(should)\b", re.IGNORECASE), "should not"),
    (re.compile(r"\b(must)\b", re.IGNORECASE), "must not"),
    (re.compile(r"\b(may)\b", re.IGNORECASE), "may not"),
    (re.compile(r"\b(are)\b", re.IGNORECASE), "are not"),
    (re.compile(r"\b(is)\b", re.IGNORECASE), "is not"),
    (re.compile(r"\b(was)\b", re.IGNORECASE), "was not"),
    (re.compile(r"\b(were)\b", re.IGNORECASE), "were not"),
    # "have not specific meanings" is not English; the do-support form is.
    (re.compile(r"\b(has)\b", re.IGNORECASE), "does not have"),
    (re.compile(r"\b(have)\b", re.IGNORECASE), "do not have"),
    (re.compile(r"\b(includes)\b", re.IGNORECASE), "does not include"),
    (re.compile(r"\b(include)\b", re.IGNORECASE), "do not include"),
    (re.compile(r"\b(requires)\b", re.IGNORECASE), "does not require"),
    (re.compile(r"\b(contains)\b", re.IGNORECASE), "does not contain"),
    (re.compile(r"\b(contain)\b", re.IGNORECASE), "do not contain"),
]


def sentence_spans(answer: str) -> list[tuple[int, int]]:
    """Start and end offsets of each sentence, so edits can be spliced in place."""
    spans, start = [], 0
    for match in SENTENCE_END.finditer(answer):
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(answer)))
    return spans


def flip_a_negation(answer: str, document: str, rng: random.Random):
    """Insert a negation into one sentence, leaving the rest of the answer byte-identical.

    The edit is spliced at absolute offsets rather than rebuilt from a sentence
    list. Rejoining sentences would also normalize whitespace, and newlines
    turning into spaces is a second change the checker can react to.
    """
    lowered = document.lower()
    spans = sentence_spans(answer)
    order = list(range(len(spans)))
    rng.shuffle(order)

    for index in order:
        start, end = spans[index]
        sentence = answer[start:end]
        # Skip sentences that are already negated; flipping those would restore a
        # claim rather than contradict one.
        if re.search(r"\b(not|never|cannot|no)\b", sentence, re.IGNORECASE):
            continue
        for pattern, replacement in FLIPS:
            match = pattern.search(sentence)
            if match is None:
                continue
            negated_sentence = sentence[: match.start()] + replacement + sentence[match.end() :]
            # The negated wording must not already appear in the source.
            if negated_sentence.lower() in lowered:
                continue
            at = start + match.start()
            return {
                "original_sentence": sentence,
                "negated_sentence": negated_sentence,
                "flipped_from": match.group(),
                "flipped_to": replacement,
                "negated_answer": answer[:at] + replacement + answer[at + len(match.group()) :],
            }
    return None


def build(n: int, seed: int) -> list[dict]:
    from datasets import load_dataset

    rows = [r for r in load_dataset(DATASET, split="test") if r["task_type"] == "QA"]
    clean = [r for r in rows if len(json.loads(r["hallucination_labels"])) == 0]
    random.Random(seed).shuffle(clean)
    rng = random.Random(seed)

    pairs = []
    for row in clean:
        edit = flip_a_negation(row["output"], row["context"], rng)
        if edit is None:
            continue
        pairs.append(
            {
                "id": str(row["id"]),
                "query": row["query"],
                "context": row["context"],
                "answer": row["output"],
                **edit,
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

    out = []
    for i, pair in enumerate(pairs, 1):
        row = dict(pair)
        row["score_original"] = token_score(pair["context"], pair["query"], pair["answer"])
        row["score_negated"] = token_score(
            pair["context"], pair["query"], pair["negated_answer"]
        )
        out.append(row)
        if i % 20 == 0:
            print(f"  {i}/{len(pairs)}", flush=True)
    return out


def report(scored: list[dict]) -> str:
    n = len(scored)
    caught = sum(1 for r in scored if r["score_negated"] > 0.5)
    false_alarms = sum(1 for r in scored if r["score_original"] > 0.5)
    added = round(
        sum(len(r["negated_sentence"]) - len(r["original_sentence"]) for r in scored) / n
    )

    numbers = json.loads((RESULTS / "numbers_scored.json").read_text())
    caught_numbers = sum(1 for r in numbers if r["score_perturbed"] > 0.5)

    lines = [
        "# Does a flipped negation get caught?\n",
        f"Model: `{MODEL}`. {n} answers annotators marked clean, each with one negation",
        f"inserted into a supported sentence. The edit adds about {added} characters and",
        "reverses the meaning of the claim.\n",
        "| Unsupported claim | size | caught |",
        "| --- | ---: | ---: |",
        "| invented passage (RAGTruth) | ~134 chars | 75 of 100 |",
        f"| flipped negation | ~{added} chars | **{caught} of {n}** |",
        f"| changed number | ~2 chars | {caught_numbers} of 100 |",
        "",
        f"False alarms on the untouched answers: {false_alarms} of {n}.",
        "",
        "## Reading it\n",
        "A low catch rate means detection tracks how much text the claim occupies rather",
        "than how wrong it is, since a negation reverses the meaning entirely. A high rate",
        "means negation is handled well and numbers are the outlier.\n",
        "## Examples\n",
        "| id | flip | untouched | negated |",
        "| --- | --- | ---: | ---: |",
    ]
    for r in scored[:10]:
        lines.append(
            f"| {r['id']} | {r['flipped_from']} -> {r['flipped_to']} "
            f"| {r['score_original']:.3f} | {r['score_negated']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["build", "score", "report"])
    parser.add_argument("--n", type=int, default=100)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)

    if args.stage == "build":
        pairs = build(args.n, args.seed)
        (RESULTS / "negation_pairs.json").write_text(json.dumps(pairs, indent=2))
        print(f"built {len(pairs)} pairs")
        for pair in pairs[:4]:
            print(f"  {pair['id']}: {pair['flipped_from']} -> {pair['flipped_to']}")

    if args.stage == "score":
        pairs = json.loads((RESULTS / "negation_pairs.json").read_text())
        scored = score(pairs)
        (RESULTS / "negation_scored.json").write_text(json.dumps(scored, indent=2))
        print(f"wrote {RESULTS / 'negation_scored.json'}")

    if args.stage == "report":
        scored = json.loads((RESULTS / "negation_scored.json").read_text())
        text = report(scored)
        (RESULTS / "negation_summary.md").write_text(text)
        print(text)


if __name__ == "__main__":
    main()
