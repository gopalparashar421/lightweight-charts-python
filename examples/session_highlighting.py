import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import SessionHighlighting

np.random.seed(9)
n = 100
dates = pd.date_range('2024-01-01 09:00', periods=n, freq='1D')
close = 100 + np.cumsum(np.random.randn(n))
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.3)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.3)
volume = np.random.randint(100_000, 500_000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

if __name__ == '__main__':
    chart = Chart()

    # Attach to the main candlestick series
    sh = SessionHighlighting(chart, default_color="#1756519E")

    # Define 3-hour morning sessions for the first three trading days
    sessions = []
    for day in pd.date_range('2024-01-01', periods=3, freq='1D'):
        start = int(pd.Timestamp(day).replace(hour=10).timestamp())
        end   = int(pd.Timestamp(day).replace(hour=13).timestamp())
        sessions.append({'start': start, 'end': end})

    chart.set(df)
    sh.set_sessions(sessions)

    chart.fit()
    chart.show(block=True)
