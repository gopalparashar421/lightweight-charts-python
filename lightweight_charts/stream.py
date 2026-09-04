"""
StreamChart — a FastAPI + WebSocket backed chart that runs as a local HTTP server.

Usage::

    from lightweight_charts import StreamChart

    chart = StreamChart()
    chart.set(df)
    chart.show(port=8080, block=True)

    # asyncio
    await chart.show_async(port=8080)

The logged URL includes a one-time security token; share it only with trusted viewers.

Reconnect model (v1.4.0+)
-------------------------
While a browser is disconnected, per-bar **transient** scripts (``series.setData`` /
``update``, volume, markers) are **not** buffered. On (re)connect the server replays a
bounded **structural** script log, then emits a data snapshot regenerated from
authoritative Python state (``candle_data`` / ``data`` / ``markers``, plus tracked
whitespace from ``append_whitespace``).

Series/marker/whitespace data is snapshot-backed. Other per-bar mutations (table
cells, price lines, legend, PositionTool P&L) still append to the structural log —
a soft size warning fires if that log grows large.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .abstract import AbstractChart, Window
from .util import BulkRunScript, parse_event_message

# ---------------------------------------------------------------------------
# Module-level constant — must match the prefix used in abstract.Window
# ---------------------------------------------------------------------------
RETURN_PREFIX = "_~_~RETURN~_~_"

_JS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js")

# Soft bound for structural script log (defense-in-depth; M-02).
_STRUCTURAL_LOG_WARN_THRESHOLD = 2000

# Library-safe logger: no handlers of our own; apps (or logging.basicConfig)
# decide where records go. NullHandler avoids "No handlers" noise.
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class StreamWindow(Window):
    """
    Drop-in replacement for abstract.Window that communicates with a browser
    client over WebSocket instead of pywebview.

    Subclasses ``Window`` so ``_id_gen``, ``create_table``, ``style``, and
    other shared window helpers stay in sync with ``AbstractChart``.

    Structural scripts are always retained in ``self.scripts`` for reconnect.
    Transient (series/marker data) scripts are never buffered — they are either
    sent live or dropped while disconnected and regenerated via snapshot.
    """

    def __init__(self) -> None:
        super().__init__()
        # Per-instance handlers (``Window.handlers`` is a shared class dict).
        self.handlers: dict = {}

        self.token: str = secrets.token_hex(32)

        self._ws: WebSocket | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._return_event = threading.Event()
        self._return_value = None
        self._server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._server_ready = threading.Event()
        self._client_ready = threading.Event()
        self._host: str | None = None
        self._port: int | None = None
        self._chart: AbstractChart | None = None
        self._data_lock = threading.RLock()
        self._structural_log_warned = False

        # Route batched JS through this window's WebSocket-aware run_script.
        self.bulk_run = BulkRunScript(self.run_script)

    def data_guard(self):
        """Real lock serializing live mutations against connect-time snapshot."""
        return self._data_lock

    def _append_structural(self, script: str) -> None:
        self.scripts.append(script)
        if not self._structural_log_warned and len(self.scripts) >= _STRUCTURAL_LOG_WARN_THRESHOLD:
            self._structural_log_warned = True
            logger.warning(
                "StreamWindow structural script log has %d entries (threshold %d). "
                "Only series/marker data is snapshot-backed; per-bar "
                "table/price-line/legend/PositionTool updates still buffer as "
                "structural and can grow unbounded.",
                len(self.scripts),
                _STRUCTURAL_LOG_WARN_THRESHOLD,
            )

    @property
    def url(self) -> str | None:
        """HTTP URL for this stream window, set after :meth:`show`."""
        if self._host is None or self._port is None:
            return None
        return f"http://{self._host}:{self._port}/"

    # ------------------------------------------------------------------
    # Public interface (mirrors abstract.Window)
    # ------------------------------------------------------------------

    def run_script(self, script: str, run_last: bool = False, transient: bool = False) -> None:
        """
        Send *script* to the connected browser, or buffer structural scripts.

        - Connected: send live; structural scripts also append to the log.
        - Disconnected + transient: drop (state lives in Python).
        - Disconnected + structural: append to ``self.scripts``.
        """
        if self.bulk_run.enabled:
            self.bulk_run.add_script(script, transient=transient)
            return
        if self._ws is not None and self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._ws.send_text(script), self._loop)
            if not transient:
                self._append_structural(script)
        else:
            if transient:
                return
            self._append_structural(script)

    def run_script_and_get(self, script: str):
        """
        Send *script* prefixed with RETURN_PREFIX, block until the browser
        evaluates it and sends back the result (timeout 5 s).
        """
        self._return_event.clear()
        self._return_value = None
        self.run_script(f"{RETURN_PREFIX}{script}")
        if not self._return_event.wait(timeout=5.0):
            raise TimeoutError(
                f"Timed out waiting for return value from browser (script: {script!r})"
            )
        return self._return_value

    def bulk_run_scripts(self, scripts) -> None:
        """Send each script in *scripts*."""
        for s in scripts:
            self.run_script(s)

    def stop(self) -> None:
        """Ask uvicorn to stop and wait for the server thread."""
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=3)

    # ------------------------------------------------------------------
    # Server startup
    # ------------------------------------------------------------------

    def show(
        self,
        title: str = "python-lightweight-charts",
        summary="",
        description="",
        port: int = 8080,
        host: str = "127.0.0.1",
        debug: bool = False,
        cors_origins: list[str] | None = None,
        log_level: str = "error",
    ) -> str:
        """Build the FastAPI app and start uvicorn in a daemon thread.

        ``log_level`` is passed to uvicorn (default ``"error"`` keeps the
        server quiet). Use ``"info"`` to surface startup and access logs via
        the host app's logging handlers. ``log_config=None`` so uvicorn does
        not call ``dictConfig`` and wipe existing handlers.
        """
        self._host = host
        self._port = port
        self._server_ready.clear()
        self._client_ready.clear()

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            self._server_ready.set()
            try:
                yield
            finally:
                self._server_ready.clear()
                self._client_ready.clear()

        app = FastAPI(
            debug=debug,
            docs_url=None,
            redoc_url=None,
            title=title,
            summary=summary,
            description=description,
            lifespan=lifespan,
        )
        allowed_origins = ["http://127.0.0.1", "http://localhost"]
        if cors_origins:
            allowed_origins.extend(cors_origins)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Explicit root route — takes priority over the static-files mount
        @app.get("/")
        async def serve_stream_html():
            headers = {
                "Content-Security-Policy": (
                    "default-src 'self'; "
                    "connect-src 'self' ws: wss:; "
                    "script-src 'self' 'unsafe-eval'; "
                    "style-src 'self' 'unsafe-inline'"
                )
            }
            return FileResponse(
                os.path.join(_JS_DIR, "stream.html"),
                headers=headers,
            )

        # Serve stream-shim.js with the session token injected
        _token = self.token

        @app.get("/stream-shim.js")
        async def serve_shim():
            with open(os.path.join(_JS_DIR, "stream-shim.js")) as f:
                content = f.read().replace("'__STREAM_TOKEN__'", repr(_token))
            from fastapi.responses import Response

            return Response(content=content, media_type="application/javascript")

        @app.websocket("/ws")
        async def ws_endpoint(websocket: WebSocket):
            await websocket.accept()

            # --- token auth ---
            try:
                first_msg = await websocket.receive_text()
            except WebSocketDisconnect:
                return
            if first_msg != self.token:
                await websocket.close(code=4001)
                return

            # --- single-client guard ---
            if self._ws is not None:
                logger.warning("A second client attempted to connect; rejected with code 4002.")
                await websocket.close(code=4002)
                return

            # H-02 / M-04: keep _ws=None during handshake so live transient
            # emits are dropped; structural replay + snapshot use ordered
            # await send_text on this event loop; flip live only after snapshot.
            for script in list(self.scripts):
                await websocket.send_text(script)

            with self.data_guard():
                snapshot_scripts: list[str] = []
                if self._chart is not None:
                    snapshot_scripts = self._chart.data_snapshot_scripts()
                for script in snapshot_scripts:
                    await websocket.send_text(script)
                self._ws = websocket

            self._client_ready.set()

            # --- message loop ---
            try:
                while True:
                    msg = await websocket.receive_text()
                    if msg.startswith(RETURN_PREFIX):
                        self._return_value = msg[len(RETURN_PREFIX) :]
                        self._return_event.set()
                    else:
                        func, args = parse_event_message(self, msg)
                        if func is not None:
                            if asyncio.iscoroutinefunction(func):
                                await func(*args)
                            else:
                                func(*args)
            except WebSocketDisconnect:
                pass
            finally:
                self._ws = None
                self._client_ready.clear()

        # Static files (bundle.js, styles.css, etc.) — mounted AFTER the
        # explicit "/" route so that route takes priority.
        app.mount("/", StaticFiles(directory=_JS_DIR), name="static")

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level=log_level,
            log_config=None,
        )
        self._server = uvicorn.Server(config)

        loop_ready = threading.Event()

        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._loop = loop
            loop_ready.set()
            try:
                loop.run_until_complete(self._server.serve())
            except OSError as exc:
                if "address already in use" in str(exc).lower() or exc.errno in (
                    98,
                    10048,
                ):
                    logger.error(
                        "Port %d is already in use. "
                        "Choose a different port with chart.show(port=<n>).",
                        port,
                    )
                else:
                    raise

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        loop_ready.wait()  # ensure self._loop is set before returning
        if not self._server_ready.wait(timeout=30.0):
            raise TimeoutError(f"Timed out waiting for chart server to start on {host}:{port}")
        return self.url or f"http://{host}:{port}/"


class StreamChart(AbstractChart):
    """
    A chart served over HTTP/WebSocket.  Open the logged URL in any browser.

    ::

        import logging
        logging.basicConfig(level=logging.INFO)

        chart = StreamChart()
        chart.set(df)
        chart.show(port=8080, block=True)
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        x: int | None = None,
        y: int | None = None,
        on_top: bool = False,
        maximize: bool = False,
        toolbox: bool = False,
    ) -> None:
        self.win = StreamWindow()
        # width/height are unused window-geometry params; pass proportions to
        # AbstractChart so autosize takes over in the browser.
        super().__init__(self.win, width=1.0, height=1.0, toolbox=toolbox)
        self.win._chart = self

    @property
    def url(self) -> str | None:
        """HTTP URL for this chart, set after :meth:`show`."""
        return self.win.url

    def show(
        self,
        port: int = 8080,
        host: str = "127.0.0.1",
        open_browser: bool = False,
        block: bool = True,
        cors_origins: list[str] | None = None,
        debug: bool = False,
        log_level: str = "error",
    ) -> str:
        """
        Start the chart server and optionally open a browser.

        Parameters
        ----------
        port:         TCP port (default 8080).
        host:         Bind address.  Use ``'0.0.0.0'`` for LAN access (see
                      security warning below).
        open_browser: Automatically open the URL in the default browser.
        block:        Block until Ctrl-C (suitable for scripts).
        cors_origins: Extra allowed CORS origins.
        debug:        Enable FastAPI debug mode.
        log_level:    Uvicorn log level (default ``"error"``). Pass ``"info"``
                      to include startup/access logs in the host logging config.
        """
        url = self.win.show(
            port=port,
            host=host,
            cors_origins=cors_origins,
            debug=debug,
            log_level=log_level,
        )
        logger.info("Chart server running at %s — press Ctrl+C to stop", url)

        if host not in ("127.0.0.1", "::1", "localhost"):
            logger.warning(
                "Chart server is accessible from the network. Ensure the token URL is kept private."
            )

        if open_browser:
            webbrowser.open(url)

        if block:
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.win.stop()
        return url

    async def show_async(
        self,
        port: int = 8080,
        host: str = "127.0.0.1",
        open_browser: bool = False,
        cors_origins: list[str] | None = None,
        debug: bool = False,
        log_level: str = "error",
    ) -> str:
        """
        Start the chart server, await readiness, and run until cancelled.

        Returns the chart URL once the server is accepting connections.
        Cancel the task or send ``KeyboardInterrupt`` to stop the server.

        Server startup (``show``) blocks the calling thread until the port is
        ready, so it runs in a worker thread via ``asyncio.to_thread`` to keep
        the caller's event loop free.
        """
        url = await asyncio.to_thread(
            self.show,
            port,
            host,
            open_browser,
            False,  # block
            cors_origins,
            debug,
            log_level,
        )
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            self.win.stop()
            return url
        except asyncio.CancelledError:
            self.win.stop()
            raise
