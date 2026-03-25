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

# Build a price-level profile from the last 50 bars
anchor_idx = n - 50
base_price = close[anchor_idx]
price_step = max(0.5, round(base_price * 0.02, 1))
n_bins = 15
profile = [
    {'price': round(base_price + i * price_step, 4),
     'vol':   float(volume[anchor_idx: anchor_idx + n_bins].mean() * np.random.uniform(0.3, 1.0))}
    for i in range(n_bins)
]

vp = VolumeProfile(
    chart,
    time=dates[anchor_idx],
    profile=profile,
    width=10,
)

chart.fit()
chart.show(block=True)
