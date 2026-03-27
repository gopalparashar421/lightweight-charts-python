import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import SessionHighlighting

np.random.seed(9)

# Intraday hourly bars: 5 business days, 09:00–17:00 UTC
days = pd.bdate_range('2024-01-02', periods=5)
times = []
for day in days:
    for hour in range(9, 18):
        times.append(pd.Timestamp(f'{day.date()} {hour:02d}:00'))
times = pd.DatetimeIndex(times)
n = len(times)

close = 100 + np.cumsum(np.random.randn(n))
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.3)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.3)
volume = np.random.randint(100_000, 500_000, n).astype(float)
df = pd.DataFrame({'time': times, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

if __name__ == '__main__':
    chart = Chart()
    chart.layout(background_color="#060709", text_color="#d1d4dc")
    chart.set(df)
    chart.candle_style(
        up_color="#9dff00",
        down_color="#ec413e"
    )
    # Attach to the main candlestick series
    sh = SessionHighlighting(chart, default_color='rgba(41, 98, 255, 0.7)')

    # Highlight 10:00–13:00 morning sessions for the first three trading days.
    # Use .value // 10**9 (nanoseconds → seconds, UTC) so timestamps are
    # consistent with how the chart converts df["time"] via astype("int64") // 10**9.
    sessions = []
    for day in days[:3]:
        start = int(pd.Timestamp(f'{day.date()} 10:00').value // 10**9)
        end   = int(pd.Timestamp(f'{day.date()} 13:00').value // 10**9)
        sessions.append({'start': start, 'end': end, 'color': 'rgba(41, 98, 255, 0.3)'})

    sh.set_sessions(sessions)

    chart.fit()
    chart.show(block=True)
