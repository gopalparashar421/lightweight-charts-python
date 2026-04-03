import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import HeatmapSeries

np.random.seed(21)
n_time = 60
n_levels = 20
dates = pd.date_range('2024-01-01', periods=n_time, freq='1h')

# Each row is one price cell: same time may appear multiple times (one row per level)
rows = []
base_price = 100.0
for ts in dates:
    for j in range(n_levels):
        low   = base_price + j * 0.5
        high  = low + 0.5
        value = round(np.random.rand() * 100, 2)  # 0–100 intensity
        rows.append({'time': ts, 'low': low, 'high': high, 'value': value})

heatmap_df = pd.DataFrame(rows)

if __name__ == '__main__':
    chart = Chart()
    heatmap = HeatmapSeries(chart, pane_index=0)
    heatmap.set(heatmap_df)

    chart.fit()
    chart.show(block=True)


## Add Example 2