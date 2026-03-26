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

if __name__ == '__main__':
    chart = Chart()
    chart.set(df)

    # Attach tooltip to the main candlestick series
    tooltip = Tooltip(
        chart,
        line_color='rgba(0, 0, 0, 0.2)',
        follow_mode='tracking',
        title='OHLCV',
    )

    chart.fit()
    chart.show(block=True)
