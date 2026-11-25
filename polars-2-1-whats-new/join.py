import polars as pl

rides = pl.scan_parquet("data/rides.parquet")
payments = pl.scan_parquet("data/payments.parquet")

tips_by_zone = (
    rides.join(payments, on="trip_id")
    .group_by("PULocationID")
    .agg(pl.col("tip_amount").mean().alias("avg_tip"))
    .collect()
)
print(tips_by_zone.shape)
