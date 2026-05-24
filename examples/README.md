# Examples

These scripts demonstrate the features added to the
[`gopalparashar421/lightweight-charts-python`](https://github.com/gopalparashar421/lightweight-charts-python)
fork of [`lightweight-charts-python`](https://github.com/louisnw01/lightweight-charts-python).

## Installation

Install from PyPI:

```bash
pip install python-lightweight-charts
```

Or clone and install in editable mode:

```bash
git clone https://github.com/gopalparashar421/lightweight-charts-python.git
cd lightweight-charts-python
pip install -e .
```

## Running the examples

Each script is self-contained — all data is generated with pandas/numpy (no
external data fetching required). Numbered examples (`1_setting_data/` through
`8_table/`) are the original tutorial series; named subdirectories are new feature demos.

```bash
# Area series
python examples/area_series/area_series.py

# Line series with last-price animation
python examples/last_price_animation/last_price_animation.py

# Attaching a custom JS primitive to a series
python examples/attach_primitive/attach_primitive.py

# Session highlighting plugin
python examples/session_highlighting/session_highlighting.py

# Floating OHLCV tooltip plugin
python examples/tooltip_plugin/tooltip_plugin.py

# Bollinger Bands using BandsIndicator plugin
python examples/bands_indicator/bands_indicator.py

# Volume-at-Price profile plugin
python examples/volume_profile/volume_profile.py

# Price-level intensity heatmap series
python examples/heatmap_series/heatmap_series.py

# Heatmap orderbook (bid/ask depth)
python examples/heatmap_orderbook/heatmap_orderbook.py

# PositionTool plugin
python examples/positions/positions.py

# StreamChart over HTTP/WebSocket
python examples/stream_chart/stream_chart.py

# Full v5 showcase: multi-pane, indicators, callbacks, table, topbar
python examples/version5_examples/version5_examples.py
```

## Feature index

| Script | Feature demonstrated |
|--------|----------------------|
| `area_series/` | `Chart.create_area()` with `top_color`, `bottom_color`, `line_color` |
| `last_price_animation/` | `create_line(last_price_animation='continuous')` |
| `attach_primitive/` | `Series.attach_primitive(js_expr)` / `AttachedPrimitive.detach()` |
| `session_highlighting/` | `plugins.SessionHighlighting` |
| `tooltip_plugin/` | `plugins.Tooltip` |
| `bands_indicator/` | `plugins.BandsIndicator` |
| `volume_profile/` | `plugins.VolumeProfile` |
| `heatmap_series/` | `plugins.HeatmapSeries` |
| `heatmap_orderbook/` | `plugins.HeatmapSeries` with orderbook bid/ask data |
| `positions/` | `plugins.PositionTool` |
| `stream_chart/` | `StreamChart` browser-served chart |
| `version5_examples/` | Multi-pane indicators, callbacks, table, topbar |
