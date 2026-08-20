"""Delete-the-evidence control: does a RAG grounding checker read the document?

Scores the same answers three times, changing only the evidence:

    baseline  the answer's own document
    shuffled  another row's document (a derangement, so no row keeps its own)
    deleted   an empty document

A checker that reads the evidence loses its skill when the evidence is wrong. One
that has learned what a hallucination *sounds like* keeps it. Which of those you
measure turns out to depend on how you collapse the checker's per-token output
into one score per answer, so this runs four collapse rules side by side.

Stages, each rerunnable on its own:

    python run_experiment.py --stage sample     build and record the sample
    python run_experiment.py --stage score      3 conditions x 4 rules, ~3 min
    python run_experiment.py --stage report     AUROC, intervals, operating points
    python run_experiment.py --stage all        all of the above
"""

from __future__ import annotations

import argparse
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

HERE = Path(__file__).parent
RESULTS = HERE / "results"
DATASET = "wandb/RAGTruth-processed"
TASK_TYPE = "QA"
MODEL = "KRLabsOrg/lettucedect-base-modernbert-en-v1"
CONDITIONS = ("baseline", "shuffled", "deleted")
RULES = ("max_span", "n_spans", "max_token", "mean_top5")
BOOTSTRAP_RESAMPLES = 2000
SPAN_THRESHOLD = 0.5


@dataclass(frozen=True)
class Case:
    """One RAGTruth row, plus the document it gets under each condition."""

    id: str
    query: str
    context: str
    answer: str
    hallucinated: bool
    shuffled_context: str

    def context_for(self, condition: str) -> str:
        return {
            "baseline": self.context,
            "shuffled": self.shuffled_context,
            "deleted": "",
        }[condition]


# --------------------------------------------------------------------------
# Sample
# --------------------------------------------------------------------------


def build_sample(n: int, seed: int) -> list[Case]:
    from datasets import load_dataset

    rows = [r for r in load_dataset(DATASET, split="test") if r["task_type"] == TASK_TYPE]

    def is_hallucinated(row) -> bool:
        labels = row["hallucination_labels"]
        if isinstance(labels, str):
            labels = json.loads(labels)
        return len(labels) > 0

    positives = [r for r in rows if is_hallucinated(r)]
    negatives = [r for r in rows if not is_hallucinated(r)]
    rng = random.Random(seed)
    rng.shuffle(positives)
    rng.shuffle(negatives)

    half = n // 2
    if len(positives) < half:
        raise SystemExit(f"only {len(positives)} hallucinated rows, need {half}")
    picked = positives[:half] + negatives[:half]
    rng.shuffle(picked)

    # Rotating by one after a shuffle guarantees a derangement: every row gets
    # somebody else's document, so `shuffled` never accidentally scores a match.
    donors = picked[1:] + picked[:1]

    return [
        Case(
            id=str(row["id"]),
            query=row["query"],
            context=row["context"],
            answer=row["output"],
            hallucinated=is_hallucinated(row),
            shuffled_context=donor["context"],
        )
        for row, donor in zip(picked, donors)
    ]


def load_sample() -> list[Case]:
    payload = json.loads((RESULTS / "sample.json").read_text())
    return [Case(**row) for row in payload["cases"]]


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def collapse(spans: list[dict], tokens: list[dict], answer: str) -> dict[str, float]:
    """Four ways to turn the checker's output into one number, plus the free baseline.

    `max_span` returns a flat 0.0 whenever no token clears the span threshold,
    which ties a large share of answers at one value. The token rules grade those
    answers instead, which is the difference the experiment is about.
    """
    probs = sorted((t["prob"] for t in tokens), reverse=True)
    return {
        "max_span": max((s["confidence"] for s in spans), default=0.0),
        "n_spans": float(len(spans)),
        "max_token": probs[0] if probs else 0.0,
        "mean_top5": float(np.mean(probs[:5])) if probs else 0.0,
        # Sees no document at any point. Included so every rule has an honest
        # yardstick: beating chance is easy, beating a word count is the question.
        "word_count": float(len(answer.split())),
    }


def score_all(cases: list[Case]) -> dict:
    from lettucedetect.models.inference import HallucinationDetector

    started = time.time()
    detector = HallucinationDetector(method="transformer", model_path=MODEL)
    print(f"loaded {MODEL} in {time.time() - started:.0f}s", flush=True)

    scores: dict[str, dict[str, dict[str, float]]] = {c: {} for c in CONDITIONS}
    for condition in CONDITIONS:
        began = time.time()
        for i, case in enumerate(cases, 1):
            kwargs = {
                "context": [case.context_for(condition)],
                "question": case.query,
                "answer": case.answer,
            }
            spans = detector.predict(**kwargs, output_format="spans")
            tokens = detector.predict(**kwargs, output_format="tokens")
            scores[condition][case.id] = collapse(spans, tokens, case.answer)
            if i % 50 == 0:
                print(f"  {condition}: {i}/{len(cases)} ({time.time() - began:.0f}s)", flush=True)
        print(f"  {condition}: done in {time.time() - began:.0f}s", flush=True)

    return {"model": MODEL, "span_threshold": SPAN_THRESHOLD, "scores": scores}


def load_scores() -> dict[str, dict[str, dict[str, float]]]:
    return json.loads((RESULTS / "scores.json").read_text())["scores"]


# --------------------------------------------------------------------------
# Metrics
# --------------------------------------------------------------------------


def bootstrap_ci(labels: np.ndarray, values: np.ndarray, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        idx = rng.integers(0, len(labels), len(labels))
        if len(set(labels[idx])) > 1:
            draws.append(roc_auc_score(labels[idx], values[idx]))
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def retained(baseline: float, condition: float) -> float:
    edge = baseline - 0.5
    return (condition - 0.5) / edge if edge > 0 else float("nan")


def operating_points(labels: np.ndarray, values: np.ndarray) -> dict[str, float]:
    """What a review queue would actually feel, which AUROC does not report."""
    fpr, tpr, _ = roc_curve(labels, values)
    usable = [(t, f) for t, f in zip(tpr, fpr) if f < 0.999]
    best_recall, at_fpr = max(usable, key=lambda p: p[0]) if usable else (0.0, 0.0)
    i = int(np.argmax(tpr >= 0.95))
    return {
        "max_reachable_recall": float(best_recall),
        "fpr_at_max_recall": float(at_fpr),
        "fpr_at_95_recall": float(fpr[i]),
        "distinct_thresholds": len(fpr),
    }


def report(cases: list[Case], scores: dict) -> str:
    labels = np.array([int(c.hallucinated) for c in cases])
    lines: list[str] = [f"# Results\n", f"Model: `{MODEL}`. {len(cases)} cases, ",
                        f"{int(labels.sum())} hallucinated / {len(labels) - int(labels.sum())} clean.\n"]

    def values_for(rule: str, condition: str) -> np.ndarray:
        return np.array([scores[condition][c.id][rule] for c in cases])

    lines.append("\n## AUROC by rule and condition\n")
    lines.append("| Rule | Condition | AUROC | 95% CI | Retained |")
    lines.append("| --- | --- | ---: | --- | ---: |")
    for rule in RULES:
        base = roc_auc_score(labels, values_for(rule, "baseline"))
        for condition in CONDITIONS:
            v = values_for(rule, condition)
            auc = roc_auc_score(labels, v)
            lo, hi = bootstrap_ci(labels, v)
            share = "-" if condition == "baseline" else f"{retained(base, auc):.0%}"
            lines.append(f"| `{rule}` | {condition} | {auc:.3f} | {lo:.3f}-{hi:.3f} | {share} |")

    wc = values_for("word_count", "baseline")
    lo, hi = bootstrap_ci(labels, wc)
    lines.append(
        f"| `word_count` | no document | {roc_auc_score(labels, wc):.3f} | {lo:.3f}-{hi:.3f} | n/a |"
    )

    lines.append("\n## Operating points, own document\n")
    lines.append("| Rule | Max reachable recall | at FPR | FPR at 95% recall | Distinct thresholds |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for rule in RULES:
        op = operating_points(labels, values_for(rule, "baseline"))
        reachable = "unreachable" if op["fpr_at_95_recall"] >= 0.999 else f"{op['fpr_at_95_recall']:.2f}"
        lines.append(
            f"| `{rule}` | {op['max_reachable_recall']:.2f} | {op['fpr_at_max_recall']:.2f} "
            f"| {reachable} | {op['distinct_thresholds']} |"
        )

    lines.append("\n## How often the checker flags anything\n")
    lines.append("| Condition | Answers with at least one span |")
    lines.append("| --- | ---: |")
    for condition in CONDITIONS:
        flagged = int((values_for("n_spans", condition) > 0).sum())
        lines.append(f"| {condition} | {flagged} of {len(cases)} |")

    lines.append("\n## Is span count a length proxy?\n")
    for condition in CONDITIONS:
        r = np.corrcoef(values_for("n_spans", condition), wc)[0, 1]
        lines.append(f"- `n_spans` vs answer length, {condition}: {r:.2f}")
    lines.append(f"- answer length vs label: {np.corrcoef(wc, labels)[0, 1]:.2f}")

    lines.append("\n## The answers `max_span` cannot separate\n")
    quiet = values_for("max_span", "baseline") == 0.0
    quiet_tokens = values_for("max_token", "baseline")[quiet]
    quiet_labels = labels[quiet]
    lines.append(
        f"- `max_span` returns exactly 0.0 for **{int(quiet.sum())} of {len(cases)}** answers "
        f"({int(quiet_labels.sum())} hallucinated, {len(quiet_labels) - int(quiet_labels.sum())} clean)"
    )
    lines.append(
        f"- `max_token` grades those same answers from {quiet_tokens.min():.3f} to {quiet_tokens.max():.3f}"
    )
    if len(set(quiet_labels)) > 1:
        lines.append(
            f"- within that group alone, `max_token` separates them at AUROC "
            f"{roc_auc_score(quiet_labels, quiet_tokens):.3f}"
        )

    lines.append("\n## Answer length by label\n")
    for name, mask in (("hallucinated", labels == 1), ("clean", labels == 0)):
        lines.append(f"- {name}: median {int(np.median(wc[mask]))} words")

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["sample", "score", "report", "all"])
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    RESULTS.mkdir(exist_ok=True)
    stage = args.stage

    if stage in ("sample", "all"):
        cases = build_sample(args.n, args.seed)
        (RESULTS / "sample.json").write_text(
            json.dumps(
                {
                    "dataset": DATASET,
                    "split": "test",
                    "task_type": TASK_TYPE,
                    "seed": args.seed,
                    "n": len(cases),
                    "n_hallucinated": sum(c.hallucinated for c in cases),
                    "cases": [asdict(c) for c in cases],
                },
                indent=2,
            )
        )
        print(f"sampled {len(cases)} cases ({sum(c.hallucinated for c in cases)} hallucinated)")

    if stage in ("score", "all"):
        payload = score_all(load_sample())
        (RESULTS / "scores.json").write_text(json.dumps(payload, indent=2))
        print(f"wrote {RESULTS / 'scores.json'}")

    if stage in ("report", "all"):
        text = report(load_sample(), load_scores())
        (RESULTS / "summary.md").write_text(text)
        print(text)



if __name__ == "__main__":
    main()
