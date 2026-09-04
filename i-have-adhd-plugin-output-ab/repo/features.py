"""Feature pipeline for daily sales."""

from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "sales.csv"


def load_sales() -> pd.DataFrame:
    """Read the raw order table."""
    return pd.read_csv(DATA, parse_dates=["order_date"])


def daily_revenue(df: pd.DataFrame) -> pd.DataFrame:
    """Total revenue per day, with the weekday name attached."""
    daily = (
        df.groupby("order_date")
        .agg(revenue=("amount", "sum"))
    )
    daily["day_of_week"] = daily["order_date"].dt.day_name()
    return daily


def rolling_average(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """Rolling mean of daily revenue over `window` days."""
    out = df.sort_values("order_date").copy()
    out["revenue_7d"] = out["revenue"].rolling(window=window, min_periods=1).mean()
    return out


def flag_large_orders(df: pd.DataFrame, threshold: float = 500.0) -> pd.DataFrame:
    """Return only the large orders, tagged."""
    large = df[df["amount"] > threshold]
    large["is_large"] = True
    return large


def main() -> None:
    orders = load_sales()
    daily = daily_revenue(orders)
    print(rolling_average(daily).tail())


if __name__ == "__main__":
    main()
