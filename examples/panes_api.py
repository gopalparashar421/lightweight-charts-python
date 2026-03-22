import pandas as pd
import numpy as np
from lightweight_charts import Chart

np.random.seed(5)
n = 80
dates = pd.date_range('2024-01-01', periods=n, freq='1D')
close = 100 + np.cumsum(np.random.randn(n))
open_ = close - np.abs(np.random.randn(n) * 0.3)
high = np.maximum(open_, close) + np.abs(np.random.randn(n) * 0.3)
low = np.minimum(open_, close) - np.abs(np.random.randn(n) * 0.3)
volume = np.random.randint(100_000, 1_000_000, n).astype(float)
df = pd.DataFrame({'time': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})

chart = Chart()
chart.set(df)

# Add a new pane for volume
chart.add_pane(height=100)
pane_count = chart.get_pane_count()
print(f'Number of panes: {pane_count}')

# Add volume histogram in pane 1
hist = chart.create_histogram(name='volume', pane_index=1, scale_margin_top=0.1, scale_margin_bottom=0.0)
vol_df = df[['time', 'volume']].rename(columns={'volume': 'value'})
hist.set(vol_df)

chart.fit()
chart.show(block=True)
