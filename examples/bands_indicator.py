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

chart = Chart()
chart.set(df)

# BandsIndicator auto-computes ±10% bands from the main series
bands = BandsIndicator(
    chart,
    line_color='rgb(25, 200, 100)',
    fill_color='rgba(25, 200, 100, 0.15)',
    line_width=1,
)

chart.fit()
chart.show(block=True)
