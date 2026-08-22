"""Does scoring one sentence at a time catch the negations the whole answer hides?

The negation test showed that a meaning-reversing edit of about four characters
gets caught far less often than an invented passage of about 134. If detection
tracks how much of the text is unsupported, then shrinking the text should help:
score each sentence against the source on its own, and take the worst score.

Same 100 answers as run_negation.py, so the two numbers are directly comparable.
Both error rates are reported, because isolating a sentence removes context the
rest of the answer was supplying, which can turn a supported claim into a
false alarm.

    python run_sentences.py --stage score     whole answer vs worst sentence
    python run_sentences.py --stage edited    the edited sentence on its own
    python run_sentences.py --stage report
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

HERE = Path(__file__).parent
RESULTS = HERE / "results"
MODEL = "KRLabsOrg/lettucedect-base-modernbert-en-v1"
THRESHOLD = 0.5

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def sentences(answer: str) -> list[str]:
    """Split an answer into scorable pieces, dropping fragments too short to judge."""
    return [piece for piece in SENTENCE_END.split(answer) if len(piece.strip()) > 15]


def score(pairs: list[dict]) -> list[dict]:
    from lettucedetect.models.inference import HallucinationDetector

    started = time.time()
    detector = HallucinationDetector(method="transformer", model_path=MODEL)
    print(f"loaded {MODEL} in {time.time() - started:.0f}s", flush=True)

    def token_score(context: str, question: str, answer: str) -> float:
        tokens = detector.predict(
            context=[context], question=question, answer=answer, output_format="tokens"
        )
        return max((token["prob"] for token in tokens), default=0.0)

    def worst_sentence(context: str, question: str, answer: str) -> float:
        pieces = sentences(answer)
        if not pieces:
            return token_score(context, question, answer)
        return max(token_score(context, question, piece) for piece in pieces)

    out = []
    for i, pair in enumerate(pairs, 1):
        row = dict(pair)
        row["whole_original"] = token_score(pair["context"], pair["query"], pair["answer"])
        row["whole_negated"] = token_score(
            pair["context"], pair["query"], pair["negated_answer"]
        )
        row["sentence_original"] = worst_sentence(
            pair["context"], pair["query"], pair["answer"]
        )
        row["sentence_negated"] = worst_sentence(
            pair["context"], pair["query"], pair["negated_answer"]
        )
        row["n_sentences"] = len(sentences(pair["answer"]))
        out.append(row)
        if i % 10 == 0:
            print(f"  {i}/{len(pairs)}", flush=True)
    return out


def report(scored: list[dict]) -> str:
    n = len(scored)

    def rate(key: str) -> int:
        return sum(1 for r in scored if r[key] > THRESHOLD)

    whole_caught, whole_false = rate("whole_negated"), rate("whole_original")
    sent_caught, sent_false = rate("sentence_negated"), rate("sentence_original")
    pieces = sum(r["n_sentences"] for r in scored) / n

    lines = [
        "# Does sentence-level scoring catch small edits?\n",
        f"Model: `{MODEL}`. The same {n} answers as the negation test, each with one",
        "negation inserted into a supported sentence. Averaging",
        f"{pieces:.1f} sentences per answer.\n",
        "| Scored as | negation caught | untouched answer flagged |",
        "| --- | ---: | ---: |",
        f"| one whole answer | {whole_caught} of {n} | {whole_false} of {n} |",
        f"| sentence at a time | **{sent_caught} of {n}** | **{sent_false} of {n}** |",
        "",
        f"Catch rate moved {sent_caught - whole_caught:+d}, "
        f"false alarms moved {sent_false - whole_false:+d}.",
        "",
        "## Where the two methods disagree\n",
        f"- negations only the sentence view caught: "
        f"{sum(1 for r in scored if r['sentence_negated'] > THRESHOLD >= r['whole_negated'])}",
        f"- negations only the whole-answer view caught: "
        f"{sum(1 for r in scored if r['whole_negated'] > THRESHOLD >= r['sentence_negated'])}",
        f"- clean answers only the sentence view flagged: "
        f"{sum(1 for r in scored if r['sentence_original'] > THRESHOLD >= r['whole_original'])}",
        "",
        "## Examples\n",
        "| id | flip | whole (clean/negated) | sentences (clean/negated) |",
        "| --- | --- | ---: | ---: |",
    ]
    for r in scored[:12]:
        lines.append(
            f"| {r['id']} | {r['flipped_from']} -> {r['flipped_to']} "
            f"| {r['whole_original']:.3f} / {r['whole_negated']:.3f} "
            f"| {r['sentence_original']:.3f} / {r['sentence_negated']:.3f} |"
        )
    return "\n".join(lines) + "\n"


def score_edited_sentence(pairs: list[dict]) -> list[dict]:
    """Score only the sentence that was edited, clean version against flipped.

    The most favorable case for the shrink-the-window idea: no other sentence can
    dominate the maximum, and the pair differs by exactly the negation.
    """
    from lettucedetect.models.inference import HallucinationDetector

    detector = HallucinationDetector(method="transformer", model_path=MODEL)

    def token_score(context: str, question: str, answer: str) -> float:
        tokens = detector.predict(
            context=[context], question=question, answer=answer, output_format="tokens"
        )
        return max((token["prob"] for token in tokens), default=0.0)

    out = []
    for i, pair in enumerate(pairs, 1):
        out.append(
            {
                "id": pair["id"],
                "edited_clean": token_score(
                    pair["context"], pair["query"], pair["original_sentence"]
                ),
                "edited_flipped": token_score(
                    pair["context"], pair["query"], pair["negated_sentence"]
                ),
            }
        )
        if i % 25 == 0:
            print(f"  {i}/{len(pairs)}", flush=True)
    return out


def sweep(scored: list[dict]) -> str:
    """What does moving the flag threshold actually buy on this error class?"""
    lines = [
        "## Does a lower threshold help?\n",
        "| threshold | negations caught | untouched answers flagged |",
        "| ---: | ---: | ---: |",
    ]
    for t in (0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01):
        caught = sum(1 for r in scored if r["whole_negated"] > t)
        false_alarms = sum(1 for r in scored if r["whole_original"] > t)
        lines.append(f"| {t} | {caught} of {len(scored)} | {false_alarms} of {len(scored)} |")
    lines += [
        "",
        "Each step down buys roughly as many false alarms as catches, so no threshold",
        "separates a flipped negation from a clean answer.",
        "",
    ]
    return "\n".join(lines)


def paired(scored: list[dict]) -> str:
    """Is the flip visible when each answer is compared against its own clean twin?

    Three aggregations of the same token scores, so the difference between them is
    the aggregation and nothing else.
    """
    n = len(scored)
    whole = sum(1 for r in scored if r["whole_negated"] > r["whole_original"])
    worst = sum(1 for r in scored if r["sentence_negated"] > r["sentence_original"])

    edited = json.loads((RESULTS / "edited_sentence_scored.json").read_text())
    alone = sum(1 for r in edited if r["edited_flipped"] > r["edited_clean"])

    return "\n".join(
        [
            "## Direction, not magnitude\n",
            "How often the flipped copy scored above its own clean twin. Chance is 50.\n",
            "| Scored as | flipped copy ranked higher |",
            "| --- | ---: |",
            f"| one whole answer | {whole} of {n} |",
            f"| worst of its sentences | {worst} of {n} |",
            f"| the edited sentence alone | {alone} of {len(edited)} |",
            "",
            "Taking the worst sentence lands near chance because the highest-scoring",
            "sentence is usually not the edited one, so the flip never moves the number.",
            "Scoring the edited sentence by itself ranks it correctly four times out of",
            "five. The checker registers the flip; collapsing the answer to one flag",
            "throws that away. Ranking against a known-correct twin is not something",
            "production has, which is why this is a diagnosis and not a fix.",
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["score", "edited", "report"])
    args = parser.parse_args()

    if args.stage == "score":
        pairs = json.loads((RESULTS / "negation_pairs.json").read_text())
        scored = score(pairs)
        (RESULTS / "sentences_scored.json").write_text(json.dumps(scored, indent=2))
        print(f"wrote {RESULTS / 'sentences_scored.json'}")

    if args.stage == "edited":
        pairs = json.loads((RESULTS / "negation_pairs.json").read_text())
        scored = score_edited_sentence(pairs)
        (RESULTS / "edited_sentence_scored.json").write_text(json.dumps(scored, indent=2))
        print(f"wrote {RESULTS / 'edited_sentence_scored.json'}")

    if args.stage == "report":
        scored = json.loads((RESULTS / "sentences_scored.json").read_text())
        text = report(scored) + "\n" + sweep(scored) + "\n" + paired(scored)
        (RESULTS / "sentences_summary.md").write_text(text)
        print(text)


if __name__ == "__main__":
    main()
