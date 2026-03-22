import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import VolumeProfile

np.random.seed(17)
n = 100
dates = pd.date_range('2024-01-01', periods=n, freq='1D')
close = 100 + np.cumsum(np.random.randn(n) * 0.5)
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.3)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.3)
volume = np.random.randint(100_000, 1_000_000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

chart = Chart()
chart.set(df)

vp = VolumeProfile(chart,
                   up_color='rgba(38, 166, 154, 0.5)',
                   down_color='rgba(239, 83, 80, 0.5)',
                   width_factor=0.35)
vp.set_data(df)

chart.fit()
chart.show(block=True)
