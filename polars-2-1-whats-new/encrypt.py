import polars as pl

trips = pl.read_parquet("data/taxi.parquet").select(
    "tpep_pickup_datetime", "PULocationID", "trip_distance", "fare_amount", "tip_amount"
)

footer_key = b"footer-key-16byt"  # keys must be 16 or 32 bytes
payment_key = b"payment-key-16by"
payment_columns = {"fare_amount": payment_key, "tip_amount": payment_key}

encryption = pl.ParquetEncryptionProperties(
    footer_key=footer_key,
    column_keys=payment_columns,
    plaintext_footer=True,
)
trips.write_parquet("data/trips_encrypted.parquet", encryption=encryption)

# Columns without a key are readable by anyone
print(pl.read_parquet("data/trips_encrypted.parquet", columns=["PULocationID", "trip_distance"]).head(3))

# Payment columns need the key
try:
    pl.read_parquet("data/trips_encrypted.parquet", columns=["PULocationID", "fare_amount"])
except pl.exceptions.ComputeError as error:
    print(error)

decryption = pl.ParquetDecryptionProperties(footer_key=footer_key, column_keys=payment_columns)
print(
    pl.read_parquet("data/trips_encrypted.parquet", decryption=decryption)
    .select("PULocationID", "fare_amount", "tip_amount")
    .head(3)
)
