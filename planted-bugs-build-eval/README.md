# Does Claude find the bugs in a broken eval?

Companion code for [`topics/planted-bugs-build-eval.md`](../../topics/planted-bugs-build-eval.md).

## How to rerun

```bash
cp -r eval ~/router-eval      # hand the skill a copy with no answer key nearby
cd ~/router-eval
python3 run_eval.py           # baseline, about 0.60
claude                        # then: /claude-api build-eval
```

Every model call goes through `claude -p` (see `eval/llm.py`), so it runs on a Claude subscription.

## Files

| Path | What it holds |
| --- | --- |
| `eval/` | the broken eval handed to the skill: cases, router, grader, runner |
| `answer_key.md` | the 5 planted bugs and what counts as catching each |
| `scripts/check_grader_flips.py` | regrades stored answers to confirm the grader flips |
| `data/case_sources.json` | the Banking77 row and intent behind each case; the full test split is on [PolyAI's GitHub](https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv) (CC-BY-4.0) |
