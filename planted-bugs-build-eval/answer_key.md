# Answer key: the 5 planted bugs

Written 2026-10-07, before any skill run. Keep this file out of the folder handed to the skill.

| # | Bug | Where | Counts as caught when the report |
| --- | --- | --- | --- |
| 1 | Wrong label | `cases.json`, case_09 "I forgot my password" expects `billing`; correct is `account` | names case_09 or its label as suspect |
| 2 | Fits two queues | `cases.json`, case_12 "i was charged when i used a us issued card..." expects `top-up`; `billing` is equally defensible | names case_12 as unclear or arguable |
| 3 | Too easy | `cases.json`, 12 of 15 are short and contain a word that gives away the queue | says most cases are trivial, or there is no headroom once grading is fixed |
| 4 | Flaky grader | `grader.py` rates queue and reason together on 1-5 and passes only a 5 | reports different verdicts on the same output, or replaces the judge for that reason |
| 5 | Answers in prompt | `router.py` worked examples are case_03, case_07, case_11 copied verbatim | names the worked examples as copies of test cases |

Mechanism check (`scripts/check_grader_flips.py`, 2026-10-07): baseline 9/15 = 0.60; 8/15 cases changed pass/fail across 4 gradings; case_09 failed every grading.
