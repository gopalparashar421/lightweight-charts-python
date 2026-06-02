# Plugins Tutorial

`python-lightweight-charts` ships six plugins that extend the chart with extra
visualisations. All plugins are available from the `lightweight_charts.plugins` module.

```python
from lightweight_charts.plugins import (
    Tooltip,
    BandsIndicator,
    SessionHighlighting,
    HeatmapSeries,
    VolumeProfile,
    PositionTool,
)
```

---

## Tooltip

`Tooltip` attaches a floating OHLCV panel that follows the crosshair. It automatically
switches the chart crosshair to Magnet mode so the tooltip snaps to the nearest bar.

```python
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import Tooltip

if __name__ == '__main__':
    chart = Chart()
    df = pd.read_csv('ohlcv.csv')
    chart.set(df)

    tooltip = Tooltip(chart.candle_series)

    chart.show(block=True)
```

To customise the tooltip after creation:

```python
tooltip.apply_options(line_color='rgba(100, 200, 255, 0.4)', title='AAPL')
```

---

## BandsIndicator

`BandsIndicator` draws a coloured fill between upper and lower band data — perfect for
Bollinger Bands, Keltner Channels, or any envelope indicator. Pass DataFrames with
`time` and `value` columns directly; the plugin manages its own internal series.

```python
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import BandsIndicator

if __name__ == '__main__':
    chart = Chart()
    df = pd.read_csv('ohlcv.csv')
    chart.set(df)

    mid = df['close'].rolling(20).mean()
    std = df['close'].rolling(20).std()
    upper_df = pd.DataFrame({'time': df['time'], 'value': (mid + 2 * std).values})
    lower_df = pd.DataFrame({'time': df['time'], 'value': (mid - 2 * std).values})

    bands = BandsIndicator(chart, upper_df, lower_df,
                           fill_color='rgba(50, 200, 100, 0.1)')

    chart.show(block=True)
```

---

## SessionHighlighting

`SessionHighlighting` shades the chart background for specific time ranges, making it
easy to identify trading sessions such as London or New York open.

```python
import pandas as pd
from datetime import datetime, timezone
from lightweight_charts import Chart
from lightweight_charts.plugins import SessionHighlighting

def to_unix(dt_str):
    return int(datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc).timestamp())

if __name__ == '__main__':
    chart = Chart()
    df = pd.read_csv('ohlcv_1h.csv')   # hourly data works best for session views
    chart.set(df)

    highlighting = SessionHighlighting(chart.candle_series)
    highlighting.set_sessions([
        {'start': to_unix('2024-01-02 08:00'), 'end': to_unix('2024-01-02 16:30'),
         'color': 'rgba(255, 200, 50, 0.1)'},   # London session
        {'start': to_unix('2024-01-02 13:30'), 'end': to_unix('2024-01-02 20:00'),
         'color': 'rgba(50, 150, 255, 0.1)'},   # NY session
    ])

    chart.show(block=True)
```

---

## HeatmapSeries

`HeatmapSeries` renders a price-level heatmap — ideal for order-book liquidity maps.
Each bar is a set of price cells with associated intensity (size) values.

```python
import pandas as pd
import numpy as np
from lightweight_charts import Chart
from lightweight_charts.plugins import HeatmapSeries

if __name__ == '__main__':
    chart = Chart()
    df = pd.read_csv('ohlcv.csv')
    chart.set(df)

    heatmap = HeatmapSeries(chart)

    # Set a single snapshot (orderbook-style)
    price_levels = np.arange(150, 160, 0.5)
    bids = [(p, np.random.uniform(100, 1000)) for p in price_levels if p < 155]
    asks = [(p, np.random.uniform(100, 1000)) for p in price_levels if p >= 155]

    heatmap.set(df.iloc[0]['time'], bids, asks)

    chart.show(block=True)
```

---

## VolumeProfile

`VolumeProfile` renders a horizontal volume-at-price histogram anchored at a specific
bar, showing where volume was traded across price levels.

```python
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import VolumeProfile

if __name__ == '__main__':
    chart = Chart()
    df = pd.read_csv('ohlcv.csv')
    chart.set(df)

    # Build profile: bucket closes into 20 price bins
    bins = pd.cut(df['close'], bins=20)
    profile = (df.groupby(bins, observed=True)
                 .agg(price=('close', 'mean'), vol=('volume', 'sum'))
                 .dropna()
                 .reset_index(drop=True))

    vp = VolumeProfile(chart.candle_series,
                       time=df.iloc[-1]['time'],
                       profile=profile,
                       width=15)

    chart.show(block=True)
```

---

## PositionTool

`PositionTool` draws a risk/reward overlay on the chart showing the stop-loss (red) and
target (green) zones relative to the entry price.

```python
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import PositionTool

if __name__ == '__main__':
    chart = Chart()
    df = pd.read_csv('ohlcv.csv')
    chart.set(df)

    # Long position: target > entry > stop
    position = PositionTool(
        chart.candle_series,
        entry=190.00,
        stop=185.00,
        target=205.00,
        entry_time=df.iloc[-20]['time'],
    )

    chart.show(block=True)
```

Update the position as price moves:

```python
position.update(stop=187.50, target=208.00)
```

Remove the overlay when the trade is closed:

```python
position.delete()
```
