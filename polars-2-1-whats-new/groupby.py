import polars as pl

months = [f"data/yellow_tripdata_2024-{m:02d}.parquet" for m in range(1, 11)]
trips = pl.scan_parquet(months)

routes_by_hour = (
    trips.group_by(
        "PULocationID",
        "DOLocationID",
        pl.col("tpep_pickup_datetime").dt.truncate("1h").alias("pickup_hour"),
    )
    .agg(
        pl.len().alias("trips"),
        pl.col("fare_amount").mean().alias("avg_fare"),
    )
    .collect()
)
print(routes_by_hour.shape)
