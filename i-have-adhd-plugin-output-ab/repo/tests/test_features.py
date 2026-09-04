import pandas as pd

from features import daily_revenue, load_sales


def test_daily_revenue():
    daily = daily_revenue(load_sales())
    assert "revenue" in daily.columns
    assert "day_of_week" in daily.columns
