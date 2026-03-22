import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import Tooltip

np.random.seed(11)
n = 80
dates = pd.date_range('2024-01-01', periods=n, freq='1D')
close = 100 + np.cumsum(np.random.randn(n))
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.3)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.3)
volume = np.random.randint(100_000, 500_000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

chart = Chart()
chart.set(df)

tooltip = Tooltip(chart, title='OHLCV', font_size=12,
                  color='rgba(255,255,255,0.9)', background='rgba(15,15,15,0.85)')

chart.fit()
chart.show(block=True)
