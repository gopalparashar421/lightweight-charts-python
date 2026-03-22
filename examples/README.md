# Examples

These scripts demonstrate the features added to the
[`gopalparashar421/lightweight-charts-python`](https://github.com/gopalparashar421/lightweight-charts-python)
fork of [`lightweight-charts-python`](https://github.com/louisnw01/lightweight-charts-python).

## Installation

Install the fork directly from GitHub:

```bash
pip install git+https://github.com/gopalparashar421/lightweight-charts-python.git
```

Or clone and install in editable mode:

```bash
git clone https://github.com/gopalparashar421/lightweight-charts-python.git
cd lightweight-charts-python
pip install -e .
```

## Running the examples

Each script is self-contained — all data is generated with pandas/numpy (no
external data fetching required).

```bash
# Area series
python examples/area_series.py

# Up/Down markers on candlestick data
python examples/up_down_markers.py

# Line series with last-price animation
python examples/last_price_animation.py

# Attaching a custom JS primitive to a series
python examples/attach_primitive.py

# Multi-pane chart (add_pane / get_pane_count / move_pane / remove_pane)
python examples/panes_api.py

# Session highlighting plugin
python examples/session_highlighting.py

# Floating OHLCV tooltip plugin
python examples/tooltip_plugin.py

# Bollinger Bands using BandsIndicator plugin
python examples/bands_indicator.py

# Volume-at-Price profile plugin
python examples/volume_profile.py

# Price-level intensity heatmap series
python examples/heatmap_series.py
```

## Feature index

| Script | Feature demonstrated |
|--------|----------------------|
| `area_series.py` | `Chart.create_area()` with `top_color`, `bottom_color`, `line_color` |
| `up_down_markers.py` | `Chart.create_up_down_markers(series)` |
| `last_price_animation.py` | `create_line(last_price_animation='continuous')` |
| `attach_primitive.py` | `Series.attach_primitive(js_expr)` / `AttachedPrimitive.detach()` |
| `panes_api.py` | `add_pane()`, `get_pane_count()`, `move_pane()` (also see `resize_pane()`, `remove_pane()`) |
| `session_highlighting.py` | `plugins.SessionHighlighting` |
| `tooltip_plugin.py` | `plugins.Tooltip` |
| `bands_indicator.py` | `plugins.BandsIndicator` |
| `volume_profile.py` | `plugins.VolumeProfile` |
| `heatmap_series.py` | `plugins.HeatmapSeries` |
