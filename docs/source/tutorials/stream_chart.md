# StreamChart Tutorial

`StreamChart` is a drop-in replacement for `Chart` that serves the chart over HTTP/WebSocket
instead of opening a desktop window. Any browser can connect — ideal for headless servers,
WSL, SSH sessions, or remote development.

## Installation

`StreamChart` is included with the base package. FastAPI and Uvicorn are hard dependencies
and are installed automatically:

```text
pip install python-lightweight-charts
```

## Minimal Example

```python
import pandas as pd
from lightweight_charts import StreamChart

if __name__ == '__main__':
    chart = StreamChart()

    df = pd.read_csv('ohlcv.csv')   # time | open | high | low | close | volume
    chart.set(df)

    chart.show(port=8080, block=True)
```

When you run this, the console prints:

```
Chart server running at http://127.0.0.1:8080/?token=<64-hex-chars>
```

Open the URL in a browser to view the chart. The token is a 64-character hex secret
that prevents unauthorised access — keep it private.

## Auto-opening the browser

Pass `open_browser=True` to `show()` to launch the system default browser automatically:

```python
chart.show(port=8080, open_browser=True, block=True)
```

## LAN access

To expose the chart on your local network, bind to all interfaces:

```python
chart.show(host='0.0.0.0', port=8080, block=True)
```

A security reminder will be printed. Share only the printed URL (with its token) with
trusted viewers.

## CORS for custom origins

When embedding the chart from another origin (e.g. a local dev server on a different port),
pass extra allowed origins:

```python
chart.show(
    port=8080,
    cors_origins=["http://192.168.1.10:3000"],
    block=True,
)
```

`http://127.0.0.1` and `http://localhost` are always allowed.

## Live data streaming

`StreamChart` supports the same `update()` / `update_from_tick()` API as `Chart`:

```python
import time
import pandas as pd
from lightweight_charts import StreamChart

if __name__ == '__main__':
    chart = StreamChart()

    df = pd.read_csv('ohlcv.csv')
    chart.set(df)

    chart.show(open_browser=True)   # non-blocking

    next_df = pd.read_csv('next_ohlcv.csv')
    for _, row in next_df.iterrows():
        chart.update(row)
        time.sleep(0.1)
```

## Reconnect behavior

While no browser is connected, per-bar data scripts (`setData` / `update` / markers)
are **not** buffered. On (re)connect the server:

1. Replays a bounded **structural** script log (series creation, styling, drawings, …).
2. Emits a **data snapshot** from Python state (OHLC/volume, line series, markers,
   and whitespace from `append_whitespace`).

Reopening a tab after hours of disconnected streaming therefore loads from current
state instead of replaying every bar update. Same-page reconnects reload the page
so structural replay always targets a fresh JavaScript context.

**Snapshot boundary:** table cells, price lines, legend text, and PositionTool P&L
updated every bar still append to the structural log and can grow if you mutate
them per bar while disconnected.

## Asyncio

Use `show_async` when the chart shares an event loop with other coroutines:

```python
import asyncio
from lightweight_charts import StreamChart

async def main():
    chart = StreamChart()
    chart.set(df)
    await chart.show_async(port=8080, open_browser=True)

asyncio.run(main())
```

## Using plugins with StreamChart

All plugins work identically with `StreamChart`:

```python
from lightweight_charts import StreamChart
from lightweight_charts.plugins import Tooltip

chart = StreamChart()
chart.set(df)

tooltip = Tooltip(chart.candle_series)

chart.show(block=True)
```

## Key differences from `Chart`

| Feature | `Chart` | `StreamChart` |
|---------|---------|---------------|
| Window | pywebview desktop window | Any browser via HTTP |
| Display | Requires display server | Headless compatible |
| Access URL | n/a | Printed one-time token URL |
| `show()` signature | `show(block)` | `show(port, host, open_browser, block, …)` |
| `show_async()` | Yes | Yes |
| Reconnect | n/a | Structural replay + data snapshot |
| Screenshot | `chart.screenshot()` | Not supported |
| `JupyterChart` | Yes | No |
