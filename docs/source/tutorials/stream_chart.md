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
| `show()` signature | `show(block)` | `show(port, host, open_browser, block)` |
| Screenshot | `chart.screenshot()` | Not supported |
| `JupyterChart` | Yes | No |
