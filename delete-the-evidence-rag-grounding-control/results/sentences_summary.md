# Does sentence-level scoring catch small edits?

Model: `KRLabsOrg/lettucedect-base-modernbert-en-v1`. The same 100 answers as the negation test, each with one
negation inserted into a supported sentence. Averaging
5.2 sentences per answer.

| Scored as | negation caught | untouched answer flagged |
| --- | ---: | ---: |
| one whole answer | 17 of 100 | 13 of 100 |
| sentence at a time | **24 of 100** | **23 of 100** |

Catch rate moved +7, false alarms moved +10.

## Where the two methods disagree

- negations only the sentence view caught: 15
- negations only the whole-answer view caught: 8
- clean answers only the sentence view flagged: 16

## Examples

| id | flip | whole (clean/negated) | sentences (clean/negated) |
| --- | --- | ---: | ---: |
| 17282 | have -> do not have | 0.037 / 0.046 | 0.080 / 0.080 |
| 13375 | can -> cannot | 0.000 / 0.000 | 0.206 / 0.142 |
| 14132 | include -> do not include | 0.789 / 0.800 | 0.886 / 0.886 |
| 14508 | can -> cannot | 0.002 / 0.002 | 0.001 / 0.001 |
| 14506 | can -> cannot | 0.453 / 0.451 | 0.553 / 0.553 |
| 15107 | can -> cannot | 0.588 / 0.238 | 0.009 / 0.009 |
| 16416 | should -> should not | 0.134 / 0.139 | 0.004 / 0.004 |
| 15553 | should -> should not | 0.002 / 0.002 | 0.001 / 0.001 |
| 15783 | was -> was not | 0.884 / 0.999 | 0.048 / 0.967 |
| 16119 | are -> are not | 0.262 / 0.181 | 0.613 / 0.518 |
| 16058 | is -> is not | 0.757 / 0.808 | 0.608 / 0.608 |
| 15776 | can -> cannot | 0.000 / 0.020 | 0.000 / 0.001 |

## Does a lower threshold help?

| threshold | negations caught | untouched answers flagged |
| ---: | ---: | ---: |
| 0.5 | 17 of 100 | 13 of 100 |
| 0.3 | 25 of 100 | 21 of 100 |
| 0.2 | 30 of 100 | 26 of 100 |
| 0.1 | 37 of 100 | 32 of 100 |
| 0.05 | 45 of 100 | 36 of 100 |
| 0.02 | 59 of 100 | 44 of 100 |
| 0.01 | 62 of 100 | 52 of 100 |

Each step down buys roughly as many false alarms as catches, so no threshold
separates a flipped negation from a clean answer.

## Direction, not magnitude

How often the flipped copy scored above its own clean twin. Chance is 50.

| Scored as | flipped copy ranked higher |
| --- | ---: |
| one whole answer | 68 of 100 |
| worst of its sentences | 36 of 100 |
| the edited sentence alone | 78 of 100 |

Taking the worst sentence lands near chance because the highest-scoring
sentence is usually not the edited one, so the flip never moves the number.
Scoring the edited sentence by itself ranks it correctly four times out of
five. The checker registers the flip; collapsing the answer to one flag
throws that away. Ranking against a known-correct twin is not something
production has, which is why this is a diagnosis and not a fix.
