# Does a flipped negation get caught?

Model: `KRLabsOrg/lettucedect-base-modernbert-en-v1`. 100 answers annotators marked clean, each with one negation
inserted into a supported sentence. The edit adds about 4 characters and
reverses the meaning of the claim.

| Unsupported claim | size | caught |
| --- | ---: | ---: |
| invented passage (RAGTruth) | ~134 chars | 75 of 100 |
| flipped negation | ~4 chars | **17 of 100** |
| changed number | ~2 chars | 48 of 100 |

False alarms on the untouched answers: 13 of 100.

## Reading it

A low catch rate means detection tracks how much text the claim occupies rather
than how wrong it is, since a negation reverses the meaning entirely. A high rate
means negation is handled well and numbers are the outlier.

## Examples

| id | flip | untouched | negated |
| --- | --- | ---: | ---: |
| 17282 | have -> do not have | 0.037 | 0.046 |
| 13375 | can -> cannot | 0.000 | 0.000 |
| 14132 | include -> do not include | 0.789 | 0.800 |
| 14508 | can -> cannot | 0.002 | 0.002 |
| 14506 | can -> cannot | 0.453 | 0.451 |
| 15107 | can -> cannot | 0.588 | 0.238 |
| 16416 | should -> should not | 0.134 | 0.139 |
| 15553 | should -> should not | 0.002 | 0.002 |
| 15783 | was -> was not | 0.884 | 0.999 |
| 16119 | are -> are not | 0.262 | 0.181 |
