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

___


```{py:method} show(port: int, host: str, open_browser: bool, block: bool)

Starts the FastAPI/Uvicorn server and optionally opens the system browser.

* `port` *(int, default 8080)*: TCP port to listen on.
* `host` *(str, default "127.0.0.1")*: Bind address. Use `"0.0.0.0"` for LAN access (a security reminder is printed).
* `open_browser` *(bool, default False)*: Open the default browser to the chart URL.
* `block` *(bool, default True)*: Block the calling thread until Ctrl+C is received.

```

````
