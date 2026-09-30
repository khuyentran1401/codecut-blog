# How should you ask a model to update your README with the fewest mistakes?

Companion code for [`topics/readme-update-from-release-notes.md`](../../topics/readme-update-from-release-notes.md).

## The problem

When a project ships several releases, the README can drift away from the release notes because keeping it current takes time.

The quick fix is to hand both files to a model and ask for an updated README.

But the model may miss real changes, promote details users do not need, or remove sections that are still useful.

This article tests which prompt helps a model update a README with the fewest mistakes.

## The versions compared

We compare five versions of asking a model to update a README. To understand each version, let's look at an example from the release notes:

```text
* Add `--config` flag to specify path to pyproject.toml configuration file.
```

**All at once**: the model gets the old README and all the release notes in one request, and is asked to **update** the README.

```text
send     Here is our README: <347 lines>
         Here are the release notes for 2.12 to 2.15: <13 lines>
         Return the updated README in full, as markdown only.
get      the whole README back, edited however the model chose
```

**Full rewrite**: the model gets the old README and all the release notes in one request, and is asked to **write a new** README from them.

```text
send     Write the README for vulture from these sources.
         Source 1, the project's previous README: <347 lines>
         Source 2, the release notes for 2.12 to 2.15: <13 lines>
get      a new README, written from nothing
```

**Section by section**: the model goes through the README one section at a time. For each section, it reads all the release notes and decides whether they change that section; if yes, it rewrites that one section.

```text
for each section:
  1. check     "Does anything in the release notes change this section?"
  2. rewrite   only if the check says yes

## Configuration   check -> yes   rewrite -> the --config flag is added
## Error codes     check -> no    left exactly as it was
```

**Change by change**: the release notes are first split into smaller changes. Each change is then sent to the README section it belongs in, and only those sections are rewritten.

```text
split     "Vulture 2.12 adds a --config flag to specify the path to a pyproject.toml file."
          "Vulture includes `tests/**/*.toml` files in its sdist."

route     --config  -> ## Configuration
          sdist     -> a section, so it gets written in

rewrite   Rewrite this README section to include the new changes. Change nothing else.
```

**Change by change, screened**: the same, but each change is checked against the README before it is sent to a section.

```text
split     "Vulture 2.12 adds a --config flag to specify the path to a pyproject.toml file."
          "Vulture includes `tests/**/*.toml` files in its sdist."

check 1   Is it already in the README, or does it contradict it?                <- added
          --config  -> no, keep
          sdist     -> no, keep
check 2   Does a user of vulture, reading its README, need this?                <- added
          --config  -> yes, keep
          sdist     -> no, drop

route     --config  -> ## Configuration
          sdist     (dropped, never routed)

rewrite   Rewrite this README section to include the new changes. Change nothing else.
```

Prompts are shown in plain words; the exact wording is in `scripts/run.py`.

## Setup

- README: vulture at v2.11 (347 lines, MIT license)
- New information: vulture's release notes for 2.12 to 2.15, 13 lines
- Model: `qwen3.8:27b-mlx` through Ollama 0.34.4
- Settings: temperature 1 (the model's default), thinking off, 3 runs per version
- Hardware and date: MacBook Pro M5 Pro, 64 GB, 2026-09-29

The release notes are labeled by hand in `inputs/release_note_labels.json`:

```text
clear home (3)        --config flag, SSLContext whitelist, while True / reachability handling
judgment call (3)     Python 3.13/3.14 support, type hints for get_unused_code, PyPI badges
maintainers only (3)  ruff, tox replaced by pre-commit, tests in the sdist
```

## How to rerun

```bash
ollama pull qwen3.8:27b-mlx
for v in all_at_once section_by_section change_by_change change_by_change_screened full_rewrite; do
  for r in 1 2 3; do
    VERSION=$v RUN=$r python3 scripts/run.py
  done
done

# score one output
python3 scripts/check_readme.py inputs/readme_v2.11.md \
  results/change_by_change/run1.md inputs/release_note_labels.json
```

## Findings

The table shows run 1 of each version. Runs 2 and 3 are in `results/<version>/run2.md` and `run3.md`.

| Version | Real changes added, of 3 | Maintainer notes added, of 3 | Old README kept | Time per update |
| --- | ---: | ---: | ---: | ---: |
| All at once | 1 | 0 | 84% | about 1.5 min |
| Full rewrite | 1 | 0 | 78%, lost a section | about 1.5 min |
| Section by section | 1 | 0 | 96% | about 1 min |
| Change by change | 3 | 3 | 88% | about 2 min |
| Change by change, screened | 2 | 1 | 95% | about 3.5 min |

Time per update is the average of the 3 runs. Section by section varied the most: in run 2 it pasted the whole changelog near the top of the README instead of editing any section.

## One worked example

This line from the release notes only matters to maintainers, so it should stay out of the README. Here is what each version did with it in run 1:

```text
* Include `tests/**/*.toml` in sdist (Colin Watson).
```

**All at once**: left it out, along with most of the real changes.

```text
(not in the README)
```

**Full rewrite**: left it out.

```text
(not in the README)
```

**Section by section**: left it out.

```text
(not in the README)
```

**Change by change**: added it, rewritten as a README sentence.

```text
- Colin Watson included `tests/**/*.toml` in the sdist.
```

**Change by change, screened**: left it out. The screening step asked "Does a user of vulture, reading its README, need this?" and dropped it before it reached a section.

```text
(not in the README)
```

## Files

| File | What it holds |
| --- | --- |
| `scripts/run.py` | all five versions |
| `scripts/check_readme.py` | where each labeled change landed, flags checked against `--help`, maintainer items, and changed lines |
| `inputs/readme_v2.11.md` | vulture's README at v2.11, the starting point |
| `inputs/release_notes_2.12_to_2.15.md` | the release notes for 2.12 to 2.15 |
| `inputs/release_note_labels.json` | the hand labels: clear home, judgment call, or maintainers only |
| `results/<version>/run1.md` to `run3.md` | the README each run produced, for each of the five versions |
| `results/runs.csv` | seconds and model calls for every run |

vulture is MIT licensed.

## References

- [Knowledge Pull Requests for Continual Document Authoring](https://arxiv.org/abs/2609.26634) (Martin and Van Durme, 2026). The four step-by-step versions follow its method and baselines: section by section is its ConText, change by change is ConClaim, change by change, screened is KPR, and full rewrite is Scratch.
