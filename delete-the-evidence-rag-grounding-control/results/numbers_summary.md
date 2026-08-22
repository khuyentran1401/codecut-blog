# Wrong-number diagnostic

Model: `KRLabsOrg/lettucedect-base-modernbert-en-v1`. 100 clean answers, each paired with a copy where
one grounded number was changed to a value absent from the source.

## Can the checker tell the two apart?

- changed answers flagged above 0.5: **48 of 100**
- untouched answers flagged above 0.5: 16 of 100
- pairs where the changed copy scored higher: 89 of 100
- pairs where both scored identically: 0 of 100

## Did it point at the number?

- perturbed answers with a flagged span covering the edited number: **34 of 100**

## Examples

| id | number | changed to | original score | perturbed score | number flagged |
| --- | --- | --- | ---: | ---: | --- |
| 13375 | 15 | 25 | 0.000 | 0.010 | no |
| 16058 | 16 | 26 | 0.757 | 0.972 | yes |
| 14288 | 72 | 12 | 0.096 | 0.289 | no |
| 14802 | 35 | 15 | 0.003 | 0.859 | yes |
| 16907 | 50 | 51 | 0.352 | 0.842 | yes |
| 15732 | 79 | 19 | 0.000 | 0.011 | no |
| 14352 | 15 | 10 | 0.000 | 0.527 | no |
| 12707 | 10 | 20 | 0.002 | 0.285 | no |
| 12347 | 10 | 30 | 0.125 | 0.465 | no |
| 12134 | 175 | 105 | 0.004 | 0.453 | no |
| 13563 | 12 | 22 | 0.957 | 0.973 | yes |
| 13158 | 20 | 21 | 0.012 | 0.019 | no |

## Does a lower threshold help?

| threshold | changed numbers caught | untouched answers flagged |
| ---: | ---: | ---: |
| 0.5 | 48 of 100 | 16 of 100 |
| 0.3 | 63 of 100 | 22 of 100 |
| 0.2 | 70 of 100 | 25 of 100 |
| 0.1 | 78 of 100 | 37 of 100 |
| 0.05 | 81 of 100 | 45 of 100 |
| 0.02 | 87 of 100 | 49 of 100 |
| 0.01 | 92 of 100 | 58 of 100 |

Unlike the negation case, recall here is genuinely for sale: 0.2 catches 70
against 48. The price is flagging a quarter of the clean answers.
