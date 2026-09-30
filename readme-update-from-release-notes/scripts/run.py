"""Five ways to update a README from release notes, following the knowledge pull
request paper (arXiv:2609.26634) and its three baselines.

README: vulture at v2.11. New information: the release notes for 2.12 to 2.15.
Every version uses the same local model through Ollama, with thinking off.

    all_at_once        the whole README and notes in one request
    section_by_section  each section shown all the notes, rewritten if affected  (paper: ConText)
    change_by_change    notes split into single changes, each routed to a section  (paper: ConClaim)
    change_by_change_screened  the same, each change screened before routing  (paper: KPR)
    full_rewrite    a new README written from the old one and the notes       (paper: Scratch)

Each run writes results/<version>/run<N>.md and adds a row to results/runs.csv.

Usage:
    VERSION=change_by_change RUN=1 python3 scripts/run.py
"""

import json
import os
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
PROJECT = "vulture"
RELEASES = "2.12 to 2.15"
MODEL = os.environ.get("MODEL", "qwen3.8:27b-mlx")
TEMP = float(os.environ.get("TEMP", "1"))  # the model's default, as in the article

README = (HERE / "inputs" / "readme_v2.11.md").read_text()
NOTES = (HERE / "inputs" / "release_notes_2.12_to_2.15.md").read_text()
CALLS = []


def chat(prompt, schema=None):
    payload = {
        "model": MODEL, "stream": False, "think": False,
        # Keep the model loaded between calls; reloading it between steps is slow.
        "keep_alive": "30m",
        "options": {"temperature": TEMP, "num_ctx": 16384},
        "messages": [{"role": "user", "content": prompt}],
    }
    if schema:
        payload["format"] = schema
    request = urllib.request.Request("http://localhost:11434/api/chat", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=900) as response:
        content = json.loads(response.read())["message"]["content"]
    CALLS.append(1)
    return json.loads(content) if schema else content


def strip_fence(text):
    """The model sometimes wraps a markdown answer in a ```markdown fence."""
    match = re.match(r"^```(?:markdown|md)?\n(.*)\n```\s*$", text.strip(), re.S)
    return match.group(1) + "\n" if match else text


def sections(markdown):
    """Split on ## and ### headings, ignoring '#' lines inside code fences."""
    parts, current, heading, fenced = [], [], "(intro)", False
    for line in markdown.splitlines(keepends=True):
        if line.startswith("```"):
            fenced = not fenced
        if not fenced and re.match(r"^#{2,3} ", line):
            parts.append((heading, "".join(current)))
            heading, current = line.strip(), []
        current.append(line)
    parts.append((heading, "".join(current)))
    return parts


CLAIMS = {"type": "object", "properties": {"claims": {"type": "array", "items": {"type": "string"}}},
          "required": ["claims"]}


def decompose(text, what):
    """Split text into single, standalone facts."""
    prompt = (f"Split this {what} into atomic, standalone factual claims about {PROJECT}. "
              "Each claim must make sense on its own, with no 'it' or 'this'. "
              f"Skip badges, links lists, and table-of-contents lines.\n\n{text}")
    return chat(prompt, CLAIMS)["claims"]


def all_at_once():
    """The whole README and notes in one request."""
    return strip_fence(chat(f"Here is our README:\n\n{README}\n\nHere are the release notes for {RELEASES}:\n\n{NOTES}\n\n"
                            "Return the updated README in full, as markdown only.").strip())


def section_by_section():
    """ConText: each relevant section is rewritten from the raw release notes."""
    schema = {"type": "object", "properties": {"relevant": {"type": "boolean"}}, "required": ["relevant"]}
    parts = []
    for heading, body in sections(README):
        if body.strip() and chat(f"README section:\n{body}\n\nRelease notes:\n{NOTES}\n\n"
                                 "Does anything in the release notes change what this section should say?",
                                 schema)["relevant"]:
            body = strip_fence(chat("Rewrite this README section to reflect the release notes. "
                                    "Change nothing else. Return the section as markdown only.\n\n"
                                    f"Section:\n{body}\n\nRelease notes:\n{NOTES}")).rstrip("\n") + "\n\n"
        parts.append(body)
    return "".join(parts)


def route_all(facts, headings):
    """Send every fact to a section, with no screening."""
    schema = {"type": "object", "properties": {"section": {"type": "string"}}, "required": ["section"]}
    routed = {}
    for fact in facts:
        prompt = ("README sections:\n" + "\n".join(headings) + f"\n\nFact: {fact}\n\n"
                  "Return the exact heading of the section this fact belongs in, "
                  "or a new '## ...' heading if none fits.")
        routed.setdefault(chat(prompt, schema)["section"].strip(), []).append(fact)
    return routed


def rewrite_routed(readme_parts, routed):
    """Rewrite only the sections that received facts; new headings become new sections at the end."""
    routed = {k: list(v) for k, v in routed.items()}
    new_parts = []
    for heading, body in readme_parts:
        facts = routed.pop(heading, None)
        if facts:
            prompt = ("Rewrite this README section to include the new facts. Change nothing else. "
                      f"Return the section as markdown only.\n\nSection:\n{body}\n\nNew facts:\n"
                      + "\n".join(f"- {f}" for f in facts))
            body = strip_fence(chat(prompt)).rstrip("\n") + "\n\n"
        new_parts.append((heading, body))
    for heading, facts in routed.items():
        prompt = (f"Write a short README section with the heading '{heading}' stating these facts, "
                  "as markdown only:\n" + "\n".join(f"- {f}" for f in facts))
        new_parts.append((heading, strip_fence(chat(prompt)).rstrip("\n") + "\n\n"))
    return "".join(body for _, body in new_parts)


def change_by_change():
    """ConClaim: split the notes into facts and route every one."""
    parts = sections(README)
    return rewrite_routed(parts, route_all(decompose(NOTES, "release notes"), [h for h, _ in parts]))


def change_by_change_screened():
    """KPR (the paper's method): split into facts, screen each against the README, route and rewrite only what passes."""
    source_claims = decompose(NOTES, "release notes")
    readme_parts = sections(README)
    readme_claims = []
    for heading, body in readme_parts:
        if body.strip():
            readme_claims += decompose(body, f"README section '{heading}'")

    # Screen 1: is the fact already covered by, or in conflict with, the README?
    label_schema = {"type": "object", "properties": {
        "status": {"type": "string", "enum": ["covered", "conflict", "absent"]},
        "readme_claim": {"type": "string"}}, "required": ["status", "readme_claim"]}
    readme_list = "\n".join(f"- {c}" for c in readme_claims)
    labels = []
    for claim in source_claims:
        prompt = (f"README claims:\n{readme_list}\n\nNew claim: {claim}\n\n"
                  "Label the new claim: 'covered' if a README claim already states it, "
                  "'conflict' if it contradicts a README claim, otherwise 'absent'. "
                  "Quote the README claim involved, or '' if absent.")
        labels.append({"claim": claim, **chat(prompt, label_schema)})

    # Screen 2: does a README reader need it?
    relevance_schema = {"type": "object", "properties": {"relevant": {"type": "boolean"}},
                        "required": ["relevant"]}
    for entry in labels:
        if entry["status"] == "absent":
            prompt = (f"Claim: {entry['claim']}\n\nDoes a user of {PROJECT}, reading its README, "
                      "need this? Answer false for maintainer-only changes such as packaging "
                      "metadata, CI, or edits to other documentation pages.")
            entry["relevant"] = chat(prompt, relevance_schema)["relevant"]

    # Route what passed, hold conflicts back, and rewrite only the routed sections.
    headings = [h for h, _ in readme_parts]
    route_schema = {"type": "object", "properties": {"section": {"type": "string"}},
                    "required": ["section"]}
    routed = {}
    for entry in labels:
        if entry.get("relevant"):
            prompt = ("README sections:\n" + "\n".join(headings) + f"\n\nClaim: {entry['claim']}\n\n"
                      "Return the exact heading of the section this claim belongs in, "
                      "or a new '## ...' heading if none fits.")
            entry["section"] = chat(prompt, route_schema)["section"].strip()
            routed.setdefault(entry["section"], []).append(entry["claim"])
    return rewrite_routed(readme_parts, routed), labels


def full_rewrite():
    """Scratch: write a new README from all sources, without editing the old one."""
    return strip_fence(chat(f"Write the README for {PROJECT} from these sources.\n\n"
                            f"Source 1, the project's previous README:\n\n{README}\n\n"
                            f"Source 2, the release notes for {RELEASES}:\n\n{NOTES}\n\n"
                            "Return the README in full, as markdown only."))


if __name__ == "__main__":
    import time
    version, run = os.environ["VERSION"], os.environ.get("RUN", "1")
    started = time.time()
    if version == "change_by_change_screened":
        readme, labels = change_by_change_screened()
    else:
        readme = {"all_at_once": all_at_once, "section_by_section": section_by_section, "change_by_change": change_by_change, "full_rewrite": full_rewrite}[version]()
    folder = HERE / "results" / version
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"run{run}.md").write_text(readme)
    if version == "change_by_change_screened":
        # Every screening decision, so a reader can see what was dropped and why.
        (folder / f"run{run}_decisions.json").write_text(json.dumps(labels, indent=2))
    log = HERE / "results" / "runs.csv"
    if not log.exists():
        log.write_text("version,run,seconds,model_calls\n")
    with log.open("a") as handle:
        handle.write(f"{version},{run},{round(time.time() - started)},{len(CALLS)}\n")
