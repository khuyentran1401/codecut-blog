import duckdb
import narwhals as nw
import pandas as pd
import polars as pl
import pytest
from datafusion import SessionContext
from narwhals.testing import assert_frame_equal

from store_sales import data, ffill_by_store, last_sale_per_store

df_polars = pl.DataFrame(data)
BACKENDS = {
    "pandas": lambda: pd.DataFrame(data),
    "polars": lambda: pl.DataFrame(data),
    "polars_lazy": lambda: pl.LazyFrame(data),
    "duckdb": lambda: duckdb.sql("SELECT * FROM df_polars"),
    "datafusion": lambda: SessionContext().from_pydict(data),
}


def to_polars(df_native):
    return nw.from_native(df_native).lazy().collect(backend="polars")


@pytest.mark.parametrize("make_df", BACKENDS.values(), ids=BACKENDS.keys())
def test_ffill_by_store(make_df):
    expected = nw.from_native(pl.DataFrame({**data, "sales": [1100, 1100, 1450, 501, 500, 500]}))
    assert_frame_equal(to_polars(ffill_by_store(make_df())), expected, check_row_order=False)


@pytest.mark.parametrize("make_df", BACKENDS.values(), ids=BACKENDS.keys())
def test_last_sale_after_ffill(make_df):
    expected = nw.from_native(pl.DataFrame({"store": ["Paro", "Thimphu"], "sales": [500, 1450]}))
    result = last_sale_per_store(ffill_by_store(make_df()))
    assert_frame_equal(to_polars(result), expected, check_row_order=False)
