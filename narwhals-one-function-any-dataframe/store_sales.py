"""Store-sales helpers that accept pandas, Polars, DuckDB, or DataFusion dataframes."""

from datetime import datetime

import narwhals as nw
from narwhals.typing import IntoFrameT

data = {
    "sale_date": [datetime(2025, 5, day) for day in (22, 23, 24, 22, 23, 24)],
    "store": ["Thimphu"] * 3 + ["Paro"] * 3,
    "sales": [1100, None, 1450, 501, 500, None],
}


def ffill_by_store(df_native: IntoFrameT) -> IntoFrameT:
    """Fill missing sales with the previous value from the same store."""
    return (
        nw.from_native(df_native)
        .with_columns(
            nw.col("sales")
            .fill_null(strategy="forward")
            .over("store", order_by="sale_date")
            .cast(nw.Int64)
        )
        .to_native()
    )


def latest_sale_per_store(df_native: IntoFrameT) -> IntoFrameT:
    """Keep each store's most recent row."""
    return (
        nw.from_native(df_native)
        .filter(nw.col("sale_date") == nw.col("sale_date").max().over("store"))
        .to_native()
    )


def last_sale_per_store(df_native: IntoFrameT) -> IntoFrameT:
    """Return each store's last sales value by date."""
    return (
        nw.from_native(df_native)
        .group_by("store")
        .agg(nw.col("sales").last(order_by="sale_date"))
        .sort("store")
        .to_native()
    )
