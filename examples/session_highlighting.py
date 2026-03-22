import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import SessionHighlighting

np.random.seed(9)
n = 100
dates = pd.date_range('2024-01-01 09:00', periods=n, freq='1H')
close = 100 + np.cumsum(np.random.randn(n))
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.3)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.3)
volume = np.random.randint(100_000, 500_000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

chart = Chart()
chart.set(df)

# Define 3 sessions: each 3 hours in the first 3 days
sessions = []
for day in pd.date_range('2024-01-01', periods=3, freq='1D'):
    start = int(pd.Timestamp(day).replace(hour=10).timestamp())
    end = int(pd.Timestamp(day).replace(hour=13).timestamp())
    sessions.append({'start': start, 'end': end})

sh = SessionHighlighting(chart, session_color='rgba(41, 98, 255, 0.08)')
sh.set_sessions(sessions)

chart.fit()
chart.show(block=True)
