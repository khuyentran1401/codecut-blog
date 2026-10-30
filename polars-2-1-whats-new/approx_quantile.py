import sys

import polars as pl

months = [f"data/yellow_tripdata_2024-{m:02d}.parquet" for m in range(1, 11)]
fares = pl.scan_parquet(months)

exact = pl.col("fare_amount").quantile(0.5).alias("exact_median")
approx = pl.col("fare_amount").approx_quantile(0.5).alias("approx_median")

# Pass "exact" or "approx" to time one method on its own
methods = {"exact": [exact], "approx": [approx]}
selected = methods.get(sys.argv[1] if len(sys.argv) > 1 else "", [exact, approx])

print(fares.select(selected).collect())
