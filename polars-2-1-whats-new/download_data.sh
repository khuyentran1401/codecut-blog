#!/usr/bin/env bash
# Download Jan to Oct 2024 NYC yellow taxi trips and the zone lookup into data/
set -euo pipefail
mkdir -p data
base=https://d37ci6vzurychx.cloudfront.net
for month in 01 02 03 04 05 06 07 08 09 10; do
  curl -sSfo "data/yellow_tripdata_2024-${month}.parquet" "${base}/trip-data/yellow_tripdata_2024-${month}.parquet"
done
cp data/yellow_tripdata_2024-01.parquet data/taxi.parquet
curl -sSfo data/taxi_zones.csv "${base}/misc/taxi_zone_lookup.csv"
