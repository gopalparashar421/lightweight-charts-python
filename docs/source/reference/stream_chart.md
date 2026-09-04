# `StreamChart`

````{py:class} StreamChart(width: int, height: int, toolbox: bool)

`StreamChart` serves a fully-featured chart over HTTP/WebSocket so it can be viewed in any browser without opening a desktop window. It is a drop-in replacement for `Chart` for headless, remote-development, or notebook environments.

The class inherits every method from `AbstractChart` (candlestick data, line/area/histogram series, plugins, pane management, etc.).

```python
from lightweight_charts import StreamChart

chart = StreamChart()
chart.set(df)       # same API as Chart
chart.show(port=8080, block=True)
```

Running the script prints a URL like:

```
Chart server running at http://127.0.0.1:8080/?token=<64-hex-chars>
```

Open the URL in any browser. The token is a one-time secret — keep it private.

> **Tip:** the printed URL is a one-time CSRF-like token; do not expose it publicly.
> To open the browser automatically, pass `open_browser=True` to `show()`.

### Reconnect model

While disconnected, per-bar data scripts are dropped (not buffered). On connect the
server replays structural setup scripts, then a data snapshot from Python state
(series OHLC/values, markers, tracked whitespace). Same-page reconnects reload the
tab for a clean JavaScript context. See the [StreamChart tutorial](../tutorials/stream_chart.md)
for the snapshot boundary.

___


```{py:method} show(port: int, host: str, open_browser: bool, block: bool, cors_origins: list[str], debug: bool)

Starts the FastAPI/Uvicorn server and optionally opens the system browser.
Returns the chart URL once the server is accepting connections.

* `port` *(int, default 8080)*: TCP port to listen on.
* `host` *(str, default "127.0.0.1")*: Bind address. Use `"0.0.0.0"` for LAN access (a security reminder is printed).
* `open_browser` *(bool, default False)*: Open the default browser to the chart URL.
* `block` *(bool, default True)*: Block the calling thread until Ctrl+C is received.
* `cors_origins` *(list[str], optional)*: Additional allowed CORS origins (e.g. `"http://192.168.1.10:8080"`). `http://127.0.0.1` and `http://localhost` are always permitted.
* `debug` *(bool, default False)*: Enable FastAPI debug mode.

```

```{py:method} show_async(port: int, host: str, open_browser: bool, cors_origins: list[str], debug: bool)

Asyncio variant of `show`. Starts the server in a worker thread, returns the URL once
ready, then awaits until the task is cancelled or interrupted.

```

````
