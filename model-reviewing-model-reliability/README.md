# Can a model catch what another model made up?

Companion code for [`topics/model-reviewing-model-reliability.md`](../../topics/model-reviewing-model-reliability.md).

## The problem

When using a model to summarize a document, it might assert things the document never said.

The usual fix is to use a second model call that reads the source and the output together and takes out anything the source does not back up.

However, the second model call might also be wrong and remove something the document does support or doesn't remove something the document does not support.

This article tests whether a model can catch what another model made up.

## The experiment

1. Take 9 real council transcripts whose `qwen3:8b` summaries each contain at least one claim the transcript does not support.
2. Read every transcript and label each claim in its summary.
3. Send each summary to three general-purpose reviewers, all told: *remove anything the transcript does not support*.

| Reviewer | What it is |
| --- | --- |
| `qwen3:8b` | the summarizer reviewing its own work |
| `llama3.1:8b` | a different model, same size |
| `qwen2.5:14b` | a different model, nearly twice the size |

A claim counts as **supported** only if the transcript states it or a participant said it.

```bash
ollama pull qwen3:8b && ollama pull llama3.1:8b && ollama pull qwen2.5:14b
ollama pull bespoke-minicheck:7b
uv run scripts/natural.py          # summaries, self-review, per-claim checks
uv run scripts/label.py            # join the hand labels onto the scored claims
uv run scripts/crossmodel.py       # the other two general reviewers
uv run scripts/agree.py            # survival for every reviewer, measured identically
```

Conditions: `temperature=0`, `num_ctx=16384`, one seed, MacBook Pro M5 Pro (64 GB), run 2026-09-10.

## The findings

9 transcripts, 35 scored claims, 12 of them unsupported.

| Reviewer | Caught, of 12 | Wrongly removed, of 23 | Total removals | Precision |
| --- | ---: | ---: | ---: | ---: |
| `qwen3:8b` reviewing its own summary | 3 | 2 | 5 | 60% |
| `llama3.1:8b` | 9 | 7 | 16 | 56% |
| `qwen2.5:14b` | 6 | 2 | 8 | 75% |

## Every unsupported claim, and how many caught it

| Draft | Claim | Reviewers that caught it |
| --- | --- | --- |
| `79` | The council approved a memorandum of understanding with the Service Em | 3 of 3 |
| `125` | There is a potential for increased costs if the revised fee structure  | 3 of 3 |
| `49` | There could be challenges in maintaining the momentum of negotiations  | 2 of 3 |
| `76` | The postponed item 52 will be reviewed by the community for 90 days wi | 2 of 3 |
| `117` | No specific risks were identified in the discussion, though the approv | 2 of 3 |
| `144` | Councilwoman Gonzales will present the recommendation following her ar | 2 of 3 |
| `48` | The moratorium could impact development timelines and potentially affe | 1 of 3 |
| `48` | There is a risk that the study may take longer than expected, delaying | 1 of 3 |
| `76` | Postponing the item may delay the implementation of the shelter animal | 1 of 3 |
| `79` | Follow up on the December 1st meeting agenda to determine what items w | 1 of 3 |
| `171` | The council voted to oppose Proposition Six, which seeks to repeal the | 0 of 3 |
| `171` | Opposing Proposition Six could result in the loss of significant state | 0 of 3 |

## What worked instead

A model trained for exactly this judgment, asked one claim at a time rather than told to rewrite:

| Reviewer | Caught, of 12 | Wrongly removed, of 23 | Total removals | Precision |
| --- | ---: | ---: | ---: | ---: |
| `bespoke-minicheck:7b` | 10 | 0 | 10 | 100% |

## Files

| File | What it holds |
| --- | --- |
| `scripts/schemas.py` | The four-section summary schema |
| `scripts/run.py` | The reviewer call and the summary renderer |
| `scripts/natural.py` | Summaries, self-review, and per-claim checks |
| `scripts/crossmodel.py` | `llama3.1:8b` and `qwen2.5:14b` as reviewers |
| `scripts/label.py` | Joins the hand labels onto the scored claims |
| `scripts/agree.py` | Survival for every reviewer, measured the same way |
| `transcripts/` | 9 MeetingBank passages, CC-BY-NC-SA 4.0, non-commercial |
| `unsupported.json` | The 12 hand-labeled unsupported claims, with why each one is unsupported |

`transcripts/` and `unsupported.json` are the inputs. `unsupported.json` is the only hand-authored file here: to disagree with a label, edit it and rerun from `scripts/label.py`.

Everything under `results/` is generated and safe to delete:

| Generated file | What it holds |
| --- | --- |
| `results/outputs/` | The self-review output for each transcript |
| `results/claims.json` | One row per claim: section, checker verdict, self-review survival |
| `results/perclaim.json` | The scored claims with the hand label joined on |
| `results/crossmodel.json` | The other two reviewers' output, keyed `model|draft` |
| `results/reviewers.json` | One row per claim with every reviewer's verdict, the source of every number above |
