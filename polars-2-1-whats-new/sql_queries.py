import polars as pl

trips = pl.scan_parquet("data/taxi.parquet")
ctx = pl.SQLContext(trips=trips)

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

# Count trips per hour with DATE_TRUNC
hourly_query = """
SELECT
    DATE_TRUNC('hour', tpep_pickup_datetime) AS pickup_hour,
    COUNT(*) AS trips
FROM trips
WHERE PULocationID = 12
  AND tpep_pickup_datetime >= '2024-01-02'
  AND tpep_pickup_datetime < '2024-01-03'
GROUP BY pickup_hour
ORDER BY pickup_hour
"""
hourly = ctx.execute(hourly_query, eager=True)
print(hourly.height)
print(hourly.head(3))

# Fill missing hours with generate_series
filled_query = """
WITH hourly AS (
    SELECT
        DATE_TRUNC('hour', tpep_pickup_datetime) AS pickup_hour,
        COUNT(*) AS trips
    FROM trips
    WHERE PULocationID = 12
      AND tpep_pickup_datetime >= '2024-01-02'
      AND tpep_pickup_datetime < '2024-01-03'
    GROUP BY pickup_hour
)
SELECT h.pickup_hour, COALESCE(hourly.trips, 0) AS trips
FROM generate_series(
    TIMESTAMP '2024-01-02 00:00:00',
    TIMESTAMP '2024-01-02 23:00:00',
    INTERVAL '1 hour'
) AS h(pickup_hour)
LEFT JOIN hourly ON h.pickup_hour = hourly.pickup_hour
ORDER BY h.pickup_hour
"""
filled = ctx.execute(filled_query, eager=True)
print(filled.height)
print(filled.slice(7, 4))
