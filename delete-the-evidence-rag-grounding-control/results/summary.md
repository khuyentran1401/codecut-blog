# Results

Model: `KRLabsOrg/lettucedect-base-modernbert-en-v1`. 200 cases, 
100 hallucinated / 100 clean.


## AUROC by rule and condition

| Rule | Condition | AUROC | 95% CI | Retained |
| --- | --- | ---: | --- | ---: |
| `max_span` | baseline | 0.844 | 0.790-0.889 | - |
| `max_span` | shuffled | 0.581 | 0.501-0.657 | 23% |
| `max_span` | deleted | 0.561 | 0.483-0.643 | 18% |
| `n_spans` | baseline | 0.816 | 0.755-0.868 | - |
| `n_spans` | shuffled | 0.673 | 0.603-0.745 | 55% |
| `n_spans` | deleted | 0.672 | 0.597-0.745 | 55% |
| `max_token` | baseline | 0.912 | 0.868-0.947 | - |
| `max_token` | shuffled | 0.581 | 0.501-0.657 | 20% |
| `max_token` | deleted | 0.561 | 0.483-0.643 | 15% |
| `mean_top5` | baseline | 0.912 | 0.868-0.947 | - |
| `mean_top5` | shuffled | 0.581 | 0.503-0.658 | 20% |
| `mean_top5` | deleted | 0.564 | 0.482-0.645 | 15% |
| `word_count` | no document | 0.717 | 0.645-0.784 | n/a |

## Operating points, own document

| Rule | Max reachable recall | at FPR | FPR at 95% recall | Distinct thresholds |
| --- | ---: | ---: | ---: | ---: |
| `max_span` | 0.75 | 0.13 | unreachable | 24 |
| `n_spans` | 0.75 | 0.13 | unreachable | 10 |
| `max_token` | 1.00 | 0.89 | 0.36 | 52 |
| `mean_top5` | 1.00 | 0.86 | 0.33 | 56 |

## How often the checker flags anything

| Condition | Answers with at least one span |
| --- | ---: |
| baseline | 88 of 200 |
| shuffled | 196 of 200 |
| deleted | 198 of 200 |

## Is span count a length proxy?

- `n_spans` vs answer length, baseline: 0.41
- `n_spans` vs answer length, shuffled: 0.42
- `n_spans` vs answer length, deleted: 0.42
- answer length vs label: 0.37

## The answers `max_span` cannot separate

- `max_span` returns exactly 0.0 for **112 of 200** answers (25 hallucinated, 87 clean)
- `max_token` grades those same answers from 0.000 to 0.472
- within that group alone, `max_token` separates them at AUROC 0.810

## Answer length by label

- hallucinated: median 136 words
- clean: median 97 words
