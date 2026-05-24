# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
