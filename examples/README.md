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
external data fetching required). Examples `1_setting_data/` through `8_table/`
are the original tutorial series; `9_area_series/` through `18_full_example/`
demonstrate new features added in this fork.

> **Note:** `AttachedPrimitive` (custom JS primitives attached to a series) is
> documented in the [API reference](../docs/source/reference/series.md) but does
> not have a standalone runnable example.

```bash
# Area series
python examples/9_area_series/area_series.py

# Line series with last-price animation
python examples/10_last_price_animation/last_price_animation.py

# Session highlighting plugin
python examples/11_session_highlighting/session_highlighting.py

# Floating OHLCV tooltip plugin
python examples/12_tooltip_plugin/tooltip_plugin.py

# Bollinger Bands using BandsIndicator plugin
python examples/13_bands_indicator/bands_indicator.py

# Volume-at-Price profile plugin
python examples/14_volume_profile/volume_profile.py

# Heatmap orderbook (bid/ask depth)
python examples/15_heatmap_orderbook/heatmap_orderbook.py

# PositionTool plugin
python examples/16_positions/positions.py

# StreamChart over HTTP/WebSocket
python examples/17_stream_chart/stream_chart.py

# Full showcase: multi-pane, indicators, callbacks, table, topbar
python examples/18_full_example/full_example.py
```

## Feature index

| Script | Feature demonstrated |
|--------|----------------------|
| `9_area_series/` | `Chart.create_area()` with `top_color`, `bottom_color`, `line_color` |
| `10_last_price_animation/` | `create_line(last_price_animation='continuous')` |
| `11_session_highlighting/` | `plugins.SessionHighlighting` |
| `12_tooltip_plugin/` | `plugins.Tooltip` |
| `13_bands_indicator/` | `plugins.BandsIndicator` |
| `14_volume_profile/` | `plugins.VolumeProfile` |
| `15_heatmap_orderbook/` | `plugins.HeatmapSeries` with orderbook bid/ask data |
| `16_positions/` | `plugins.PositionTool` |
| `17_stream_chart/` | `StreamChart` browser-served chart |
| `18_full_example/` | Multi-pane indicators, callbacks, table, topbar |
