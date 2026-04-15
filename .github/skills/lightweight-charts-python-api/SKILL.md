---
name: lightweight-charts-python-api
description: "API usage and code examples for the lightweight-charts-python package. Use when: writing chart code, creating series, loading data, styling charts, streaming live data, using plugins (Tooltip, BandsIndicator, SessionHighlighting, HeatmapSeries, PositionTool), adding tables, handling callbacks, building multi-pane layouts, or attaching custom primitives."
---

# lightweight-charts-python API

## When to Use
- Writing new chart scripts or adding features to existing ones
- Answering "how do I…" questions about the package
- Debugging API misuse (wrong method names, wrong data shapes, etc.)
- Adding plugins, indicators, overlays, tables, or callbacks

---

## Core Imports

```python
from lightweight_charts import Chart
# Series types returned by factory methods — no need to import separately
# Plugins live in the sub-package:
from lightweight_charts.plugins import (
    SessionHighlighting, Tooltip, BandsIndicator,
    HeatmapSeries, PositionTool, VolumeProfile,
)
```

---

## 1. Basic Setup

```python
chart = Chart()
chart.show(block=True)   # block=True keeps the process alive
# or non-blocking:
chart.show()
```

`Chart(toolbox=True)` enables the drawing toolbox.  
`Chart(title='My Chart')` sets the window title.  
`Chart(inner_height=1)` is required when using multi-pane layouts.

---

## 2. Loading OHLCV Data

DataFrame columns: `time | open | high | low | close | volume`  
`time` can be a string, `datetime`, or `pd.Timestamp`.

```python
import pandas as pd
df = pd.read_csv('ohlcv.csv')
chart.set(df)
```

Pass `True` as the second argument to `set()` to keep the current time-scale position:

```python
chart.set(new_data, True)
```

---

## 3. Series Types

### Candlestick (default — from `chart.set()`)
The main series is always candlestick. Call `chart.set(df)`.

### Line Series
```python
line = chart.create_line(
    name='SMA 50',        # Should match the column name in the DataFrame passed to line.set()
    color='#2196F3',
    width=2,
    price_line=True,      # show horizontal price line
    price_label=True,     # show price label on axis
    last_price_animation='continuous',  # or 'one_shot' / None
    pane_index=0,         # 0 = main pane
)
line.set(pd.DataFrame({'time': ..., 'SMA 50': ...}))
```

Column name in the DataFrame must match the `name` argument of `create_line`.

### Area Series
```python
area = chart.create_area(
    name='value',         # Should match the column name in the DataFrame passed to area.set()
    top_color='rgba(33, 150, 243, 0.4)',
    bottom_color='rgba(33, 150, 243, 0.0)',
    line_color='#2196F3',
    line_width=2,
)
area.set(df)   # df columns: time | value
```

### Histogram Series
```python
histogram = chart.create_histogram('MACD', pane_index=1)   # Should match the column name in the DataFrame passed to histogram.set()
histogram.set(macd_df)   # columns: time | MACD | Signal | Histogram
```

---

## 4. Styling

```python
chart.layout(
    background_color='#090008',
    text_color='#FFFFFF',
    font_size=16,
    font_family='Helvetica',
)

chart.candle_style(
    up_color='#26a69a',   down_color='#ef5350',
    wick_up_color='#26a69a', wick_down_color='#ef5350',
    border_up_color='#FFFFFF', border_down_color='#FFFFFF',
)

chart.volume_config(up_color='#26a69a', down_color='#ef5350')

chart.watermark('1D', color='rgba(180, 180, 240, 0.7)')

chart.crosshair(
    mode='normal',
    vert_color='#FFFFFF', vert_style='dotted',
    horz_color='#FFFFFF', horz_style='dotted',
)

chart.legend(visible=True, font_size=14)

chart.fit()   # zoom-to-fit all data
```

---

## 5. Live Data Streaming

### OHLCV bar-by-bar
```python
chart.set(df_initial)
chart.show()

for _, bar in df_live.iterrows():
    chart.update(bar)           # appends or updates the last bar
    sleep(0.1)
```

### Markers on streaming data
```python
chart.marker(text='Price crossed $20!')
```

### Tick data → OHLC aggregation
```python
chart.set(df_ohlc)
chart.show()

for _, tick in ticks.iterrows():
    chart.update_from_tick(tick)   # tick columns: time | price
    sleep(0.03)
```

---

## 6. Multi-Pane Layout

Use `pane_index` to place series in separate panes.  
Instantiate the chart with `Chart(inner_height=1)`.

```python
chart = Chart(inner_height=1)

# Main pane (pane_index=0 is default)
chart.set(df)
line = chart.create_line('SMA 5', pane_index=0)
line.set(sma_df)

# Sub-pane 1 — MACD histogram
histogram = chart.create_histogram('MACD', pane_index=1)
histogram.set(macd_df)
```

---

## 7. Callbacks & Topbar

```python
chart = Chart(toolbox=True)

# Topbar widgets
chart.topbar.textbox('symbol', 'TSLA')
chart.topbar.switcher('timeframe', ('1min', '5min', '30min'),
                      default='5min', func=on_timeframe_selection)

# Event hooks
chart.events.search += on_search

# Draggable horizontal line with callback
chart.horizontal_line(200, func=on_horizontal_line_move)
```

Callback signatures:
```python
def on_search(chart, searched_string): ...
def on_timeframe_selection(chart): ...
def on_horizontal_line_move(chart, line): ...  # line.price gives current price
```

Read topbar values with `chart.topbar['widget_name'].value`.

---

## 8. Plugins

All plugins are imported from `lightweight_charts.plugins`.

### Tooltip
```python
tooltip = Tooltip(
    chart,
    line_color='rgba(0, 0, 0, 0.2)',
    follow_mode='tracking',   # or 'top'
    title='OHLCV',
)
```

### BandsIndicator (Bollinger / envelope fills)
Create two transparent line series for upper and lower bands, then attach:
```python
upper = chart.create_line(color='rgba(0,0,0,0)', width=0,
                           price_line=False, price_label=False)
lower = chart.create_line(color='rgba(0,0,0,0)', width=0,
                           price_line=False, price_label=False)
upper.set(upper_df)
lower.set(lower_df)

bands = BandsIndicator(
    upper, lower,
    line_color='rgba(25, 200, 100, 0)',
    fill_color='rgba(25, 200, 100, 0.15)',
    line_width=0,
)
```

### SessionHighlighting
```python
sh = SessionHighlighting(chart, default_color='rgba(41, 98, 255, 0.7)')

# Sessions: list of dicts with UTC unix timestamps (seconds)
sessions = [
    {'start': int(start_ts.value // 10**9),
     'end':   int(end_ts.value   // 10**9),
     'color': 'rgba(41, 98, 255, 0.3)'},
    ...
]
sh.set_sessions(sessions)
```

Convert `pd.Timestamp` → unix seconds: `int(ts.value // 10**9)`

### HeatmapSeries — generic grid
```python
# heatmap_df columns: time | low | high | value
heatmap = HeatmapSeries(chart, pane_index=0)
heatmap.set(heatmap_df)
```

### HeatmapSeries — orderbook mode
Supply custom JS shaders and use `set(time, bids, asks)` / `update(time, bids, asks)`.  
`bids` and `asks` are lists of `(price_str, amount_int)` tuples.

```python
bid_shader_js = "(amount) => { ... return `rgba(...)`; }"
ask_shader_js = "(amount) => { ... return `rgba(...)`; }"

heatmap = HeatmapSeries(
    chart,
    cell_border_width=0,
    bid_shader_js=bid_shader_js,
    ask_shader_js=ask_shader_js,
    pane_index=0,
)
heatmap.set(dates[0], first_bids, first_asks)
for date, bids, asks in feed:
    heatmap.update(date, bids, asks)
```

### PositionTool
```python
from lightweight_charts import PositionTool

position = PositionTool(
    series=chart,
    entry=183.86,
    stop=175.00,
    target=202.00,
    entry_time=entry_bar['time'],
    account_balance=10_000.0,
    risk_percent=1.5,
)

# Later: update stop or target
position.update(stop=new_stop)

# Remove the overlay
position.delete()
```

---

## 9. Attaching a Custom Primitive

```python
line = chart.create_line(name='value', color='#7B68EE')
line.set(df)

primitive = line.attach_primitive(
    '({'
    '  attached: function() {},'
    '  detached: function() {},'
    '  updateAllViews: function() {},'
    '  paneViews: function() { return []; },'
    '})'
)
```

The argument is a raw JS expression that evaluates to an object implementing the `ISeriesPrimitive` interface.

---

## 10. Table

```python
table = chart.create_table(
    width=0.35, height=0.35,
    headings=('Symbol', 'Open', 'Close', 'Change %'),
    widths=(0.25, 0.25, 0.25, 0.25),
    alignments=('left', 'right', 'right', 'right'),
    position='left',
    draggable=True,
    background_color='#131722',
    border_color='rgb(50, 56, 68)', border_width=1,
    heading_text_colors=('#9598a1',) * 4,
    heading_background_colors=('#1e222d',) * 4,
    func=on_row_click,   # optional row-click callback
)

# Value format templates
table.format('Change %', f'{table.VALUE} %')
table.format('Open', f'$ {table.VALUE}')

# Header / footer sections
table.header(1)
table.header[0] = 'Market Overview'
table.footer(1)
table.footer[0] = 'Click a row to load symbol data'

# Adding rows
row = table.new_row('TSLA', 180.25, 183.40, 1.75)

# Styling individual cells
row.background_color('Change %', '#26a69a')
row.text_color('Change %', '#ffffff')
```

Row-click callback signature:
```python
def on_row_click(row):
    symbol = row['Symbol']   # access cell value by heading name
```

---

## Key Data Shape Rules

| Method | Required columns |
|--------|-----------------|
| `chart.set(df)` | `time, open, high, low, close, volume` |
| `line.set(df)` | `time, <name>` (name matches `create_line(name=...)`) |
| `area.set(df)` | `time, <name>` |
| `histogram.set(df)` | `time, <name>` + optional extra columns |
| `chart.update(series)` | same as `chart.set` — a single row/Series |
| `chart.update_from_tick(tick)` | `time, price` |
| `HeatmapSeries.set(df)` (grid) | `time, low, high, value` |
