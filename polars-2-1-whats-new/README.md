# What's New in Polars 2.1

Code for the CodeCut article "What's New in Polars 2.1: Group-Bys That Spill, Fuller SQL, and Encrypted Parquet".

## Files

```text
polars-2-1-whats-new/
├── download_data.sh   # downloads Jan to Oct 2024 NYC taxi trips and the zone lookup into data/
├── groupby.py         # route-by-hour group-by over 10 months (33M rows)
├── sql_queries.py     # read_parquet with a list of paths, DATE_TRUNC, generate_series
└── encrypt.py         # writes and reads a Parquet file with encrypted payment columns
```

## Setup

1. Install Polars 2.1:

   ```bash
   pip install polars==2.1.0
   ```

2. Download the data (about 540 MB):

   ```bash
   ./download_data.sh
   ```

## Run

```bash
python sql_queries.py
python encrypt.py
```

To compare memory with and without a spill budget (`/usr/bin/time -l` on macOS, `/usr/bin/time -v` on Linux):

```bash
/usr/bin/time -l python groupby.py
POLARS_OOC_MEMORY_BUDGET_MB=500 /usr/bin/time -l python groupby.py
```

Add `POLARS_OOC_LOG_METRICS=1` to print how much data was written to disk.

To compare with Polars 1.x, run `groupby.py` again in an environment with `polars==1.44.2`.

## Data

NYC TLC Trip Record Data: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
