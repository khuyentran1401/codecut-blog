import polars as pl

trips = pl.scan_parquet("data/taxi.parquet")

# Read several files in one table function
three_months = pl.sql(
    """
    SELECT COUNT(*) AS trips
    FROM read_parquet([
        'data/yellow_tripdata_2024-01.parquet',
        'data/yellow_tripdata_2024-02.parquet',
        'data/yellow_tripdata_2024-03.parquet'
    ])
    """,
    eager=True,
)
print(three_months)

# Round pickup times to the hour with DATE_TRUNC
rounded = pl.sql(
    """
    SELECT
        tpep_pickup_datetime,
        DATE_TRUNC('hour', tpep_pickup_datetime) AS pickup_hour
    FROM trips
    WHERE PULocationID = 12
      AND CAST(tpep_pickup_datetime AS DATE) = '2024-01-02'
    ORDER BY tpep_pickup_datetime
    LIMIT 4
    """,
    eager=True,
)
print(rounded)

# Create one row per hour with generate_series
hours = pl.sql(
    """
    SELECT *
    FROM generate_series(
        TIMESTAMP '2024-01-02 06:00:00',
        TIMESTAMP '2024-01-02 09:00:00',
        INTERVAL '1 hour'
    ) AS t(pickup_hour)
    """,
    eager=True,
)
print(hours)
