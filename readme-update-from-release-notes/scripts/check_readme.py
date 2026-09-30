"""Check an LLM-updated README against the four questions in the article.

Usage:
    python3 scripts/check_readme.py OLD.md NEW.md ITEMS.json --cli "uvx --from python-dotenv[cli]==1.2.2 dotenv"

ITEMS.json lists each release-note item with its kind ("user" or "internal") and
a regular expression that finds it. Writing that list is the one step done by hand.
"""

import argparse
import json
import re
import subprocess

# Headings a pasted changelog uses. A change found only under one of these was
# pasted in, not placed in the section it affects.
CHANGELOG_HEADING = re.compile(
    r"^#+\s*(added|changed|fixed|removed|deprecated|security|breaking changes|.*\bchanges|v?\d+\.\d+.*)\s*$",
    re.IGNORECASE,
)
FLAG = re.compile(r"(?<![\w-])--[a-z][\w-]*")


def headed_lines(markdown):
    """Yield (heading, line) for every line outside code fences' '#' comments."""
    heading, fenced = "(top)", False
    for line in markdown.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("#"):
            heading = line.strip()
        yield heading, line


def headed_paragraphs(markdown):
    """Yield (heading, paragraph), joining wrapped lines so a sentence split across lines still matches."""
    current, heading = [], "(top)"
    for h, line in headed_lines(markdown):
        if h != heading or not line.strip():
            if current:
                yield heading, " ".join(current)
            current, heading = [], h
        if line.strip():
            current.append(line.strip())
    if current:
        yield heading, " ".join(current)


def where(markdown, pattern):
    """The headings under which a pattern appears."""
    return sorted({h for h, para in headed_paragraphs(markdown) if re.search(pattern, para, re.IGNORECASE)})


def known_flags(cli):
    """Every flag the real tool accepts, from its --help and each subcommand's --help."""
    base = cli.split()
    top = subprocess.run(base + ["--help"], capture_output=True, text=True).stdout
    commands = re.findall(r"^\s{2}(\w[\w-]*)\s", top.split("Commands:")[-1], re.MULTILINE) if "Commands:" in top else []
    text = top + "".join(subprocess.run(base + [c, "--help"], capture_output=True, text=True).stdout for c in commands)
    return set(FLAG.findall(text))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("old"); parser.add_argument("new"); parser.add_argument("items")
    parser.add_argument("--cli", help="command that runs the tool, to check flags against its --help")
    args = parser.parse_args()
    old, new = open(args.old).read(), open(args.new).read()
    items = json.load(open(args.items))

    print("4.1  Did each change land in the right section?")
    user = [i for i in items if i["kind"] == "user"]
    placed = 0
    for item in user:
        spots = where(new, item["find"])
        sections = [s for s in spots if not CHANGELOG_HEADING.match(s)]
        placed += bool(sections)
        status = "placed" if sections else ("pasted only" if spots else "MISSING")
        print(f"     {status:12} {item['item']:42} {', '.join(spots) or '-'}")
    print(f"     -> {placed}/{len(user)} placed in a section")

    judgment = [i for i in items if i["kind"] == "judgment"]
    for item in judgment:
        spots = where(new, item["find"])
        print(f"     {'added' if spots else 'left out':12} {item['item']:42} {', '.join(spots) or '-'}   (judgment call)")

    print("\n4.2  Did it add anything false? (new flags checked against --help)")
    new_flags = sorted(set(FLAG.findall(new)) - set(FLAG.findall(old)))
    if args.cli:
        real = known_flags(args.cli)
        for flag in new_flags:
            print(f"     {'ok     ' if flag in real else 'UNKNOWN'} {flag}")
        print(f"     -> {sum(f not in real for f in new_flags)} unknown of {len(new_flags)} new flags")
    else:
        print(f"     new flags to check by hand: {', '.join(new_flags) or 'none'}")

    print("\n4.3  Did it add anything that doesn't belong?")
    internal = [i for i in items if i["kind"] == "internal"]
    leaked = [i for i in internal if where(new, i["find"])]
    for item in leaked:
        print(f"     LEAKED  {item['item']:42} {', '.join(where(new, item['find']))}")
    print(f"     -> {len(leaked)}/{len(internal)} internal items in the new README")

    print("\n4.4  Did it break what was already there?")
    squash = lambda s: " ".join(s.split())
    new_lines = {squash(l) for l in new.splitlines()}
    changed = [l for l in old.splitlines() if l.strip() and squash(l) not in new_lines]
    for line in changed:
        print(f"     changed: {line.strip()[:90]}")
    print(f"     -> {len(changed)} original lines changed beyond spacing (read each: an intended edit or damage?)")


if __name__ == "__main__":
    main()
