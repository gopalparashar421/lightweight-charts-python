# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
---

## [1.3.0] — 2026-06-19

### Added

- **`create_subchart(label, main_label, toolbox)`** on `AbstractChart` — returns a `SubChart` sharing the parent's webview; a tab bar appears automatically when `create_subchart` is first called. `SubChart` inherits the full `AbstractChart` API (`set`, `create_line`, `create_histogram`, etc.). Closes [#26](https://github.com/gopalparashar421/lightweight-charts-python/issues/26).
- **Drawing text labels** — `text`, `text_position`, and `text_color` on `box()`, `horizontal_line()`, `ray_line()`, and `trend_line()`; `text_h_align` / `text_v_align` on `vertical_line()`. Labels render on the chart canvas (TradingView-style). All shapes support runtime updates via `options()`.
- **`box()` text placement** — new `text_placement` argument (`"inside"` | `"outside"`, default `"outside"`) controls whether the label is drawn inside the rectangle or just outside its edge. `text_position` (`"center"`, `"left"`, `"right"`, `"top"`, `"bottom"`) still selects which side or corner to anchor the label.
- **`SeriesCommon.append_whitespace(count, bar_seconds)`** and **`Candlestick.append_whitespace(...)`** — append future whitespace bars after the last data point so drawings remain visible when resampling to a coarser timeframe.
- **`StreamChart.show(..., cors_origins=...)`** — optional list of extra allowed CORS origins for browser clients connecting from custom hosts.
- **`BandsIndicator` DataFrame support** — constructor accepts `upper_data` and `lower_data` as `pd.DataFrame` directly; internal hidden `Line` series are created automatically.

### Changed

- **`BandsIndicator` constructor** (**breaking**) — signature is now `BandsIndicator(chart, upper_data: pd.DataFrame, lower_data: pd.DataFrame, ...)`. The old `SeriesCommon` parameter interface is removed. Default `line_color` is `rgba(0,0,0,0)` (transparent) and default `line_width` is `0`.
- **`box()` label default** — box text is now drawn outside the rectangle by default (`text_placement="outside"`). Pass `text_placement="inside"` to restore the previous in-rectangle label behaviour.
- **`Candlestick.update(..., historical_update=False)`** and **`SeriesCommon.update(..., historical_update=False)`** — pass `historical_update=True` to update an existing bar by time instead of appending when future whitespace bars extend past the last real bar.
- **`SeriesCommon.update` keyword** — renamed `historicalUpdate` to `historical_update` (snake_case).

### Fixed

- **Box and trend-line drawings on resampled data** — `box()`, `trend_line()`, and related drawing helpers no longer snap coordinates to interval buckets when `round=False` (the default). Drawing times now match the epoch seconds stored by `chart.set()`, fixing collapsed shapes on weekly and monthly charts. Closes [#30](https://github.com/gopalparashar421/lightweight-charts-python/issues/30).

- **`axis_label_visible`** on `horizontal_line()` and `ray_line()` — value is now passed to JavaScript and respected by the price-axis label view.
- **StreamChart CORS** — correct `CORSMiddleware` registration and origin merging (the prior implementation used `list.append`, which returns `None`).
- **Chart JS errors** — evaluation failures in the webview subprocess are forwarded to the main process and logged with script context.
- **Topbar text widget** — pass `null` instead of an empty string when no callback is provided, preventing ASI issues in generated scripts.
- **Window script batching** — trailing semicolons when concatenating scripts prevent automatic semicolon insertion from merging adjacent statements.
- **Chart logging** — replaced `print` with the `logging` module for JavaScript error output.

---

## [1.2.0] — 2026-05-31 — Improved Legend Component

### Modified

- **`legend.ts` Settings** —

---

## [1.1.0] — 2026-05-28 — Improved Position Tool

### Added

- **`PositionTool` hover labels** — hovering the risk/reward overlay now shows entry price (blue line), TP/SL prices at left corners, R:R ratio and bar count on the entry line, and win/lose amounts at right corners; pass `quantity=N` for monetary display (`+$125.00`) or omit for price-distance display

---

## [1.0.0] — 2026-05-24 — First Public Release

First release published under the name **`python-lightweight-charts`** on PyPI,
maintained by [Gopal Parashar](https://github.com/gopalparashar421).

Forked from [`louisnw01/lightweight-charts-python`](https://github.com/louisnw01/lightweight-charts-python)
(last upstream release v2.1). Full credit to the original author [@louisnw01](https://github.com/louisnw01).
MIT licence preserved with dual copyright notice (2023 louisnw01 / 2026 Gopal Parashar).

### Added

- **LWC v5 bundle** — TypeScript/JavaScript bundle upgraded to Lightweight Charts v5.x
- **`StreamChart`** — browser-based chart served over HTTP/WebSocket (FastAPI + Uvicorn)
- **Full `IChartApi` surface** — `price_scale()`, `time_scale()`, watermark, grid, crosshair options
- **Multi-pane API** — `add_pane()`, `get_pane_count()`, `panes()`, `resize_pane()`, `remove_pane()`, `swap_panes()`
- **Six plugins** — `Tooltip`, `BandsIndicator`, `SessionHighlighting`, `HeatmapSeries`, `VolumeProfile`, `PositionTool`
- **Series enhancements** — `Area` with per-point colours, `last_price_animation`, `attach_primitive()`, `UpDownMarkers`
- **`SeriesCommon` extensions** — `position()`, `position_list()`, `vertical_span()`, `move_to_pane()`, `subscribe_data_changed()`, `set_series_order()`
- **CI/CD pipelines** — GitHub Actions workflows for lint, test, build, and PyPI publish (OIDC Trusted Publisher)
- **Pre-commit hooks** — Ruff lint/format, file hygiene, and `no-commit-to-branch main`
- New dependencies: `fastapi>=0.100,<1.0`, `uvicorn[standard]>=0.23`

### Changed

- **Package name** on PyPI renamed to `python-lightweight-charts`; import name unchanged (`from lightweight_charts import Chart`)
- **Python minimum** raised to `>= 3.10` (uses union type syntax `X | Y`)
- **Build system** migrated to `pyproject.toml` as the single source of truth

### Removed

- `setup.py` removed in favour of `pyproject.toml`

---
