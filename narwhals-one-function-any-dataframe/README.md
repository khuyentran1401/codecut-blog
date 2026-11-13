# One DataFrame Function for pandas, Polars, DuckDB, and DataFusion

Code for the CodeCut article "Write One DataFrame Function for pandas, Polars, DuckDB, and DataFusion with Narwhals".

## Files

- `store_sales.py`: three Narwhals functions (`ffill_by_store`, `latest_sale_per_store`, `last_sale_per_store`) and the six-row sample data
- `demo.py`: runs every function on every backend and prints the results
- `test_store_sales.py`: pytest suite that runs each function on pandas, Polars, Polars lazy, DuckDB, and DataFusion

## Setup

Requires Python 3.10+.

```bash
pip install "narwhals>=2.28" pandas polars duckdb pyarrow datafusion narwhals-datafusion pytest
```

Tested with narwhals 2.28.0, pandas 3.1.1, polars 2.1.0, duckdb 2.0.0, pyarrow 26.0.1, datafusion 55.0.0, and narwhals-datafusion 0.2.0.

## Run

```bash
python demo.py
```

Prints, for each backend, the type `ffill_by_store` returns, each store's latest row, and each store's last sales value after filling.

## Test

```bash
pytest -v
```
