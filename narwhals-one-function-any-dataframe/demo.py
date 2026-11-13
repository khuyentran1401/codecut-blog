"""Run each store-sales function on every backend and print the result type."""

import duckdb
import pandas as pd
import polars as pl
from datafusion import SessionContext

from store_sales import data, ffill_by_store, last_sale_per_store, latest_sale_per_store

df_polars = pl.DataFrame(data)
inputs = {
    "pandas": pd.DataFrame(data),
    "polars": df_polars,
    "polars lazy": pl.LazyFrame(data),
    "duckdb": duckdb.sql("SELECT * FROM df_polars"),
    "datafusion": SessionContext().from_pydict(data),
}

for name, df in inputs.items():
    print(f"\n=== {name}")
    print(type(ffill_by_store(df)))
    print(latest_sale_per_store(df))
    print(last_sale_per_store(ffill_by_store(df)))
