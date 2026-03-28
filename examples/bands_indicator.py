import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import BandsIndicator

np.random.seed(13)
n = 100
dates = pd.date_range('2024-01-01', periods=n, freq='1h')
close = 100 + np.cumsum(np.random.randn(n) * 0.5)
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.2)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.2)
volume = np.random.randint(100_000, 500_000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

# Compute 20-period Bollinger Bands (+/- 2 std deviations)
period = 20
sma = df['close'].rolling(period).mean()
std = df['close'].rolling(period).std()
upper_vals = (sma + 2 * std).dropna()
lower_vals = (sma - 2 * std).dropna()
upper_df = pd.DataFrame({'time': dates[period - 1:], 'value': upper_vals.values})
lower_df = pd.DataFrame({'time': dates[period - 1:], 'value': lower_vals.values})

if __name__ == '__main__':
    chart = Chart()
    chart.set(df)

    # Create line series to supply upper/lower band data.
    # Set color to transparent to hide the lines and rely on BandsIndicator for rendering.
    upper_series = chart.create_line(
        color='rgba(25, 200, 100, 0)',
        width=0,
        price_line=False,
        price_label=False,
    )
    upper_series.set(upper_df)

    lower_series = chart.create_line(
        color='rgba(25, 200, 100, 0)',
        width=0,
        price_line=False,
        price_label=False,
    )
    lower_series.set(lower_df)

    # BandsIndicator draws the fill region between upper_series and lower_series.
    # Works for Bollinger Bands, Donchian Channels, or any custom envelope.
    bands = BandsIndicator(
        upper_series,
        lower_series,
        line_color='rgba(25, 200, 100, 0)',
        fill_color='rgba(25, 200, 100, 0.15)',
        line_width=0,
    )

    chart.fit()
    chart.show(block=True)
