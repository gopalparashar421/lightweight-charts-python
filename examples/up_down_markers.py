import pandas as pd
import numpy as np
from lightweight_charts import Chart

np.random.seed(1)
n = 80
dates = pd.date_range('2024-01-01', periods=n, freq='1D')
close = 100 + np.cumsum(np.random.randn(n) * 0.5)
open_ = close - np.random.uniform(0, 1, n)
high = np.maximum(open_, close) + np.random.uniform(0, 1, n)
low = np.minimum(open_, close) - np.random.uniform(0, 1, n)
volume = np.random.randint(100000, 500000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

chart = Chart()
chart.set(df)
markers = chart.create_up_down_markers(chart, up_color='#26a69a', down_color='#ef5350')
chart.fit()
chart.show(block=True)
