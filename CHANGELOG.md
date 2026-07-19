# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
---

## [Unreleased]

---

## [1.4.0] — 2026-07-19

### Added

- **Responsive chart chrome** — legend, top bar, subchart tabs, and HTML tables scale typography (and table padding) with the embedded window size via shared CSS `clamp()` tokens (`--chrome-font-*`). Designed for roughly 480×320–2560×1440 windows at 1x/2x HiDPI. No new Python sizing knobs.
- **`StreamChart.show_async(...)`** — asyncio-friendly server start that mirrors `Chart.show_async` (non-blocking `show` under the hood, then runs until cancelled).
- **`Window.run_script(..., transient=False)`** — additive keyword used by `StreamChart` to classify per-bar data scripts; ignored by the pywebview `Chart` path.

### Changed

- **`legend(..., font_size=...)` removed** (**breaking**) — both `AbstractChart.legend` and `SeriesCommon.legend` no longer accept `font_size`. Legend type size is owned by CSS; pass content and optional `color` / `font_family` only. `layout(font_size=...)` and `watermark(font_size=...)` are unchanged (canvas/LWC, not chrome).
- **Top bar and subchart tab overflow** — when widgets/tabs no longer fit at the responsive type-scale floor, the top bar and subchart tab bar scroll horizontally instead of clipping or compressing labels.
- **`stream-shim.js` reconnect** — after an established session closes, the page `location.reload()`s for a fresh JS context (avoids duplicate `Lib.Handler` construction). Close code `4002` uses a short backoff retry instead of reload; reload attempts are bounded via `sessionStorage`.

### Fixed

- **StreamChart reconnect flood** — while disconnected, per-bar `series.update` / `setData` / marker scripts are no longer buffered. On (re)connect the server replays a bounded structural script log, then emits a data snapshot from authoritative Python state (`candle_data` / series `data` / markers / tracked whitespace), so reopen-after-hours no longer replays thousands of updates and crash the page.
- **Candlestick snapshot** — main-series reconnect data is taken from `candle_data` (full OHLC), not the empty inherited `data` frame.
- **Snapshot/live cutover** — `_ws` is set only after the snapshot is fully sent under the data guard, so bars streamed during handshake are not lost.
- **`bulk_run` tagging** — transient vs structural tags are preserved through batched flushes; purely transient batches are dropped while disconnected.
- **StreamChart CSP** — Content-Security-Policy now allows WebSocket connections (`connect-src 'self' ws: wss:`) and inline styles (`style-src 'self' 'unsafe-inline'`), so live streaming and chrome styling work under the default CSP header.
- **StreamChart WebSocket scheme** — the browser shim picks `wss://` on HTTPS pages and `ws://` otherwise, instead of always using `ws://`.
- **`StreamWindow` inheritance** — subclasses `Window` so shared helpers (`_id_gen`, tables, style) stay in sync with `AbstractChart`.
- **Volume profile data helper** — internal data path aligned between Python and the TypeScript plugin.

### Notes

- **Snapshot boundary** — series data, markers, and whitespace from `append_whitespace` are snapshot-backed on reconnect. Other per-bar mutations (table cells, price lines, legend, PositionTool P&L) still buffer as structural and can grow if updated every bar.

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
