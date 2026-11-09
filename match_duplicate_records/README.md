# Match Duplicate Records Across Sources

Companion code for the CodeCut article on matching product records with RapidFuzz, Sentence Transformers, and TypeSafe Jev.

## Files

| File | What it holds |
| --- | --- |
| `match.py` | Runs the exact-join baseline and all three steps, and prints matches found and wrong merges for each |
| `download_data.sh` | Downloads the Abt-Buy benchmark into `data/` |
| `results/jev_top3.csv` | Jev's probability for each of the 3,243 candidate pairs (written by `match.py`) |

## Setup

```bash
pip install rapidfuzz sentence-transformers typesafe-sdk pandas python-dotenv
./download_data.sh
```

Add your TypeSafe API key to a `.env` file in this folder:

```text
TYPESAFE_API_KEY=your-key
```

## Run

```bash
python match.py
```

Step 3 sends 3,243 pairs to Jev. It takes about 90 seconds and costs about $0.07.

## Data

[Abt-Buy](https://dbs.uni-leipzig.de/research/projects/benchmark-datasets-for-entity-resolution), from the University of Leipzig entity resolution benchmarks: 1,081 Abt products, 1,092 Buy products, and 1,097 known matches.
