import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import HeatmapSeries

np.random.seed(21)
n_time = 60
n_levels = 20
dates = pd.date_range('2024-01-01', periods=n_time, freq='1H')

# Build heatmap data: each row = one time point, with multiple price-level intensities
# Format: time, low, high, value  (one row per price bucket per time)
rows = []
base_price = 100.0
for i, ts in enumerate(dates):
    for j in range(n_levels):
        low = base_price + j * 0.5
        high = low + 0.5
        value = np.random.rand()  # intensity 0..1
        rows.append({'time': ts, 'low': low, 'high': high, 'value': value})

heatmap_df = pd.DataFrame(rows)

chart = Chart()
heatmap = HeatmapSeries(chart, pane_index=0)
heatmap.set(heatmap_df)

chart.fit()
chart.show(block=True)
