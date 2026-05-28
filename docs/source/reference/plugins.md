# Plugins

Plugins extend the chart with visualisations beyond the built-in series types.
Import from `lightweight_charts.plugins`.

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

## `Tooltip`

````{py:class} Tooltip(series, line_color: COLOR, follow_mode: str, title: str)

A floating tooltip that follows the crosshair and displays OHLCV price data
for the bar under the cursor. Automatically switches the chart crosshair to
Magnet mode.

* `series` — the primary series to attach the tooltip to.
* `line_color` — colour of the tooltip border line.
* `follow_mode` — `'top'` (default) or `'tracking'`.
* `title` — optional label shown at the top of the tooltip.

___

```{py:method} apply_options(line_color, follow_mode, title)

Updates tooltip display options. Only supplied arguments change.

```
___

```{py:method} delete()

Detaches and removes the tooltip from the series.

```

````

---

## `BandsIndicator`

````{py:class} BandsIndicator(upper_series, lower_series, line_color: COLOR, fill_color: COLOR, line_width: int)

Draws band lines and a filled region between an upper and lower series
(e.g. Bollinger Bands, Keltner Channels, Donchian Channels).

* `upper_series` — a `SeriesCommon`-derived series representing the upper band.
* `lower_series` — a `SeriesCommon`-derived series representing the lower band.
* `line_color` — colour of both band lines.
* `fill_color` — fill colour of the region between the bands.
* `line_width` — line width in pixels.

Example:

```python
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import BandsIndicator

chart = Chart()
df = pd.read_csv('ohlcv.csv')
chart.set(df)

mid = df['close'].rolling(20).mean()
std = df['close'].rolling(20).std()
upper_df = pd.DataFrame({'time': df['time'], 'Upper': mid + 2 * std})
lower_df = pd.DataFrame({'time': df['time'], 'Lower': mid - 2 * std})

upper = chart.create_line('Upper')
lower = chart.create_line('Lower')
upper.set(upper_df)
lower.set(lower_df)

bands = BandsIndicator(upper, lower)
chart.show(block=True)
```

___

```{py:method} delete()

Detaches and removes the bands indicator.

```

````

---

## `SessionHighlighting`

````{py:class} SessionHighlighting(series, default_color: COLOR)

Highlights the chart background for specified time ranges to mark trading sessions
(e.g. London open, New York open).

* `series` — the series to attach the highlighting to.
* `default_color` — default background colour outside sessions (default: transparent).

___

```{py:method} set_sessions(sessions: list)

Sets the time ranges to highlight.

Each entry is a dict with:

* `start` — session start as Unix seconds (int).
* `end` — session end as Unix seconds (int).
* `color` — *(optional)* CSS colour string for this session.

Example:

```python
from datetime import datetime, timezone

def to_unix(dt_str):
    return int(datetime.fromisoformat(dt_str).replace(tzinfo=timezone.utc).timestamp())

highlighting.set_sessions([
    {'start': to_unix('2024-01-01 08:00'), 'end': to_unix('2024-01-01 16:30')},
    {'start': to_unix('2024-01-01 13:30'), 'end': to_unix('2024-01-01 16:00'),
     'color': 'rgba(255, 165, 0, 0.1)'},
])
```

___

```{py:method} delete()

Detaches and removes the session highlighting.

```

````

---

## `HeatmapSeries`

````{py:class} HeatmapSeries(chart, bid_color: COLOR, ask_color: COLOR, cell_border_width: int, cell_border_color: COLOR, pane_index: int)

Custom series rendering a price-level heatmap — ideal for order-book liquidity visualisation.

* `chart` — the parent `Chart` (or `StreamChart`) instance.
* `bid_color` — base colour for bid-side cells.
* `ask_color` — base colour for ask-side cells.
* `cell_border_width` — width of cell borders in pixels.
* `cell_border_color` — colour of cell borders.
* `pane_index` — pane to place the series on.

Custom shader functions (`bid_shader_js`, `ask_shader_js`, `cell_shader_js`)
can be passed as JavaScript strings to override per-cell colouring.

___

```{py:method} set(time, bids: list, asks: list)

Replaces all heatmap data with a single orderbook snapshot.

* `time` — timestamp (Unix seconds, datetime, or string).
* `bids` — list of `(price, size)` tuples for bid levels.
* `asks` — list of `(price, size)` tuples for ask levels.

```
___

```{py:method} update(time, bids: list, asks: list)

Appends or updates the heatmap bar at the given timestamp with a new snapshot.

Same parameter format as `set()`.

```

````

---

## `VolumeProfile`

````{py:class} VolumeProfile(series, time, profile, width: int)

Renders a volume-profile histogram at a specific time position on a series.
The profile is a vertical bar chart of price levels vs. accumulated volume.

* `series` — the series to anchor the profile to.
* `time` — anchor timestamp (Unix seconds, datetime, or string).
* `profile` — price-level volume data: list of `{'price': float, 'vol': float}` dicts, or a `DataFrame` with `price` and `vol` columns.
* `width` — width of the profile in bar units (default 10).

Example:

```python
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import VolumeProfile

chart = Chart()
df = pd.read_csv('ohlcv.csv')
chart.set(df)

# Build a profile: price levels bucketed into 20 bins
bins = pd.cut(df['close'], bins=20)
profile = df.groupby(bins, observed=True).agg(
    price=('close', 'mean'),
    vol=('volume', 'sum')
).dropna().reset_index(drop=True)

vp = VolumeProfile(chart.candle_series, df.iloc[-1]['time'], profile)
chart.show(block=True)
```

___

```{py:method} delete()

Detaches and removes the volume profile.

```

````

---

## `PositionTool`

````{py:class} PositionTool(series, entry: NUM, stop: NUM, target: NUM, entry_time: TIME, end_time: TIME, stop_color: COLOR, target_color: COLOR, quantity: NUM)

Risk/reward overlay visualising an open trade position. Renders a stop zone
(red rectangle) and target zone (green rectangle) between the entry price and
stop/target prices.

Hovering over the overlay reveals an entry price line (blue) with the
following metrics:

* Entry price and bar count, shown inside the rectangle above the line.
* Risk/reward ratio (e.g. `1:2`), shown below the line.
* TP/SL prices anchored at the left inner edge of their respective zones.
* Win/lose amounts at the right inner edge — monetary (e.g. `+$125.00`) when
  `quantity` is supplied, or raw point delta otherwise.

**Price-ordering constraints:**
* Long position: `target > entry > stop`
* Short position: `stop > entry > target`

* `series` — the series to attach the overlay to.
* `entry` — entry price.
* `stop` — stop-loss price.
* `target` — take-profit price.
* `entry_time` — timestamp of entry bar.
* `end_time` — *(optional)* end timestamp; if omitted, the overlay auto-tracks the latest bar (always at least 15 bars wide from entry).
* `stop_color` / `target_color` — fill colours for each zone.
* `quantity` — *(optional)* number of units/contracts; enables monetary win/lose display. Must be `> 0`.

Example:

```python
from lightweight_charts import Chart
from lightweight_charts.plugins import PositionTool
import pandas as pd

chart = Chart()
df = pd.read_csv('ohlcv.csv')
chart.set(df)

pos = PositionTool(
    chart.candle_series,
    entry=100.0, stop=95.0, target=112.0,
    entry_time=df.iloc[10]['time'],
    quantity=10,
)
chart.show(block=True)
```

___

```{py:method} update(entry, stop, target, end_time, quantity)

Updates one or more position parameters. Only supplied arguments change;
others retain their current values.

```
___

```{py:method} delete()

Detaches and permanently removes the position overlay.

```

````
