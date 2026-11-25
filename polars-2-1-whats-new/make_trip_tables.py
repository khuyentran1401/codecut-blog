import polars as pl

months = [f"data/yellow_tripdata_2024-{m:02d}.parquet" for m in range(1, 11)]

# Copy the 33M trips three times to get about 100M
trips = pl.concat([pl.scan_parquet(months)] * 3).with_row_index("trip_id")

# Split into rides and payments tables that share trip_id
payment_columns = ["fare_amount", "tip_amount", "tolls_amount", "total_amount", "payment_type"]
trips.drop(payment_columns).sink_parquet("data/rides.parquet")
trips.select("trip_id", *payment_columns).sink_parquet("data/payments.parquet")
