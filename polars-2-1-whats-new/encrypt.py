import polars as pl

trips = pl.read_parquet("data/taxi.parquet")

# Define keys
footer_key = b"footer-key-16byt"  # keys must be 16 or 32 bytes
payment_key = b"payment-key-16by"

# Define sensitive columns
payment_columns = {"fare_amount": payment_key, "tip_amount": payment_key}

# Encrypt the file
encryption = pl.ParquetEncryptionProperties(
    footer_key=footer_key,
    column_keys=payment_columns,
    plaintext_footer=True,  # let readers without keys read the unencrypted columns
)
trips.write_parquet("data/trips_encrypted.parquet", encryption=encryption)

# Without keys, only the unencrypted columns are readable
print(pl.read_parquet("data/trips_encrypted.parquet", columns=["PULocationID", "trip_distance"]).head(3))

# With keys, the sensitive columns are readable too
decryption = pl.ParquetDecryptionProperties(footer_key=footer_key, column_keys=payment_columns)
print(
    pl.read_parquet(
        "data/trips_encrypted.parquet",
        columns=["fare_amount", "tip_amount"],
        decryption=decryption,
    ).head(3)
)
