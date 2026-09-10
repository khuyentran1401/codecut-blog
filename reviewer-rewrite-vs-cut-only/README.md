# Reviewer: rewrite vs cut only

Companion code for [`topics/reviewer-rewrite-vs-cut-only.md`](../../topics/reviewer-rewrite-vs-cut-only.md).

## The problem

Have you ever used one model to review another model's output?

Say the first model summarizes a meeting transcript. The summary looks useful, but you are not sure which claims are actually backed by the transcript. So you add a second model call: compare the transcript with the summary, then remove anything unsupported.

The problem is that the second model may not reliably remove unsupported claims.

This article tests how well that second model does the job.

## The experiment

1. Summarize three real council transcripts into four sections each.
2. Plant four false claims in each **summary**, never in the transcript, so they are guaranteed unsupported.
3. Send each summary through three reviewers, all told: *remove anything the transcript does not support*.
4. Score each on how many planted claims it removed, and of which kind.

| Planted per summary | Example |
| --- | --- |
| 1 obvious | "The council approved a $2.5 million predevelopment loan to Howard CDM" |
| 1 plausible | "Staff will report back within 60 days on the share of the tire contract" |
| 2 subtle | "There is a risk that the tire contract will be awarded entirely to out-of-state suppliers" |

| Reviewer | Returns |
| --- | --- |
| Control | nothing, the draft is left alone. Costs no model call, and checks the instrument: a planted claim must read as present here for a "removed" verdict elsewhere to mean anything |
| Free rewrite | a new summary in its own words |
| Operations only | a list of claims to remove, chosen from a fixed menu and applied by plain Python |

Both reviewers see the same numbered draft and the same untouched transcript, so the only thing that differs is what each may hand back.

Conditions: `qwen3:8b` at `temperature=0`, checker `bespoke-minicheck:7b`, one seed, run 2026-09-10.

```bash
ollama pull qwen3:8b && ollama pull bespoke-minicheck:7b
uv run scripts/generate.py   # 3 drafts from the transcripts
uv run scripts/plant.py      # hand labels + the planted claims
uv run scripts/run.py        # the three reviewer versions
uv run scripts/score.py      # checker calls behind every number
```

## The findings

Of 12 planted false claims:

| Tier | Planted | Free rewrite removed | Operations removed |
| --- | ---: | ---: | ---: |
| Obvious | 3 | 3 | 3 |
| Plausible | 3 | **1** | 2 |
| Subtle | 6 | **0** | 4 |
| **All tiers** | **12** | **4** | **9** |

**One measurement caveat, found by the control.** The checker reports that "The council approved a $2.5 million predevelopment loan to Howard CDM" is not asserted in the untouched draft, though it is there word for word. Both reviewers score as removing that claim, and both genuinely did, confirmed by reading `outputs/49/`. The other 11 planted claims read as present in the control, so their verdicts rest on the checker alone.

Everything free rewrite removed is a flat statement that something happened. Everything it kept carries a modal: "there is a risk that", "may", "could". Full numbers per claim are in `results.json`, and the walkthrough below shows one draft end to end.

## One draft, end to end

Draft `44`, a council item awarding a tire contract. Four false claims were planted in the summary, marked below. Both reviewers see the same numbered draft and the same untouched transcript.

**Control: the draft, no reviewer.**

```text
Decisions
[ 1] The council approved the motion to award contracts for new tires, not to exceed $770,000 citywide.
[ 2] The council voted to raise the local business preference to 15 percent, effective immediately.   planted, obvious

Action Items
[ 3] The council will discuss a procurement study and allocate $250,000 for it later in the day.
[ 4] The council will consider increasing local business preference in future RFPs, from 5% to 15%.
[ 5] Staff will report back within 60 days on the share of the tire contract going to Long Beach vendors.  planted, plausible

Risks
[ 6] There is a risk that local businesses may not receive a significant portion of the contract.
[ 7] The current local business preference may not be sufficient to meaningfully impact the local economy.
[ 8] There is a risk that the tire contract will be awarded entirely to out-of-state suppliers.   planted, subtle
[ 9] The council may need to revisit the contract if local participation does not improve.        planted, subtle

Open Questions
[10] How much industrial tire is the local company currently receiving under the contract?
[11] What is the current local business preference percentage in the RFPs?
```

**Free rewrite.** It removed claims 2 and 5, the two flat assertions, and kept both planted risks. Note that it renumbered what it kept, so its `[2]` is the original claim 3. Matching claims by id here would score it wrong:

```text
Decisions
[1] The council approved the motion to award contracts for new tires, not to exceed $770,000 citywide.

Action Items
[2] The council will discuss a procurement study and allocate $250,000 for it later in the day.
[3] The council will consider increasing local business preference in future RFPs, from 5% to 15%.

Open Questions
[4] How much industrial tire is the local company currently receiving under the contract?
[5] What is the current local business preference percentage in the RFPs?

Risks
[6] There is a risk that local businesses may not receive a significant portion of the contract.
[7] The current local business preference may not be sufficient to meaningfully impact the local economy.
[8] There is a risk that the tire contract will be awarded entirely to out-of-state suppliers.   still here, planted
[9] The council may need to revisit the contract if local participation does not improve.        still here, planted
```

**Operations only.** It deleted nine of the eleven claims: `2, 4, 5, 6, 7, 8, 9, 10, 11`. All four planted claims are gone, along with five of the summarizer's own:

```text
Decisions
- The council approved the motion to award contracts for new tires, not to exceed $770,000 citywide.

Action Items
- The council will discuss a procurement study and allocate $250,000 for it later in the day.
```

This draft is the extreme case for both reviewers. Free rewrite kept two fabrications. Operations caught all four and cut most of the summary doing it. On draft `49` the same two versions removed almost the same single claim, which is why the per-draft swing matters more than the totals at this sample size.

## Files

| File | What it does |
| --- | --- |
| `scripts/schemas.py` | The draft schema and the operations union, which is the intervention |
| `scripts/generate.py` | Produces one draft summary per transcript |
| `scripts/plant.py` | Hand labels, plus planted claims with their tier |
| `scripts/run.py` | Control, free rewrite, and operations only |
| `scripts/score.py` | Support and survival, both via `bespoke-minicheck` |
| `transcripts/` | The input: three real MeetingBank passages, CC-BY-NC-SA 4.0, non-commercial |
| `drafts/` | What gets reviewed: each transcript's summary as numbered claims, with hand labels and the planted false claims. `c1…cN` are the summarizer's own, `f1…f4` are planted |
| `outputs/<draft>/` | One folder per draft. `control.txt` and `free_rewrite.txt` are those reviewers' output. The restricted reviewer produces two files: `operations_only.plan.json` is what it returned, `operations_only.txt` is the summary after Python applied it |
| `results.json` | One row per claim per version, the source of every number |
