import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import BandsIndicator

np.random.seed(13)
n = 100
dates = pd.date_range('2024-01-01', periods=n, freq='1D')
close = 100 + np.cumsum(np.random.randn(n) * 0.5)
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.2)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.2)
volume = np.random.randint(100_000, 500_000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

# Compute Bollinger Bands
window = 20
rolling_mean = pd.Series(close).rolling(window).mean()
rolling_std = pd.Series(close).rolling(window).std()
upper_vals = rolling_mean + 2 * rolling_std
lower_vals = rolling_mean - 2 * rolling_std

upper_df = pd.DataFrame({'time': dates, 'value': upper_vals})
lower_df = pd.DataFrame({'time': dates, 'value': lower_vals})
upper_df = upper_df.dropna().reset_index(drop=True)
lower_df = lower_df.dropna().reset_index(drop=True)

chart = Chart()
chart.set(df)

upper_line = chart.create_line(name='Upper BB', color='#2196F3', width=1, price_line=False, price_label=False)
lower_line = chart.create_line(name='Lower BB', color='#2196F3', width=1, price_line=False, price_label=False)
upper_line.set(upper_df)
lower_line.set(lower_df)

bands = BandsIndicator(chart, upper_line, lower_line,
                       fill_color='rgba(33, 150, 243, 0.1)',
                       upper_color='#2196F3',
                       lower_color='#2196F3',
                       line_width=1)

chart.fit()
chart.show(block=True)
