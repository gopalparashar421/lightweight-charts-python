import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import BandsIndicator

np.random.seed(13)
n = 100
dates = pd.date_range("2024-01-01", periods=n, freq="1h")
close = 100 + np.cumsum(np.random.randn(n) * 0.5)
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.2)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.2)
volume = np.random.randint(100_000, 500_000, n).astype(float)
df = pd.DataFrame(
    {"time": dates, "open": open_, "high": high, "low": low, "close": close, "volume": volume}
)

# Compute 20-period Bollinger Bands (+/- 2 std deviations)
period = 20
sma = df["close"].rolling(period).mean()
std = df["close"].rolling(period).std()
upper_vals = (sma + 2 * std).dropna()
lower_vals = (sma - 2 * std).dropna()
upper_df = pd.DataFrame({"time": dates[period - 1 :], "value": upper_vals.values})
lower_df = pd.DataFrame({"time": dates[period - 1 :], "value": lower_vals.values})

if __name__ == "__main__":
    chart = Chart()
    chart.set(df)

    # BandsIndicator accepts DataFrames directly — no manual Line series needed.
    # Works for Bollinger Bands, Donchian Channels, or any custom envelope.
    bands = BandsIndicator(
        chart,
        upper_df,
        lower_df,
        fill_color="rgba(25, 200, 100, 0.15)",
    )

    chart.fit()
    chart.show(block=True)
