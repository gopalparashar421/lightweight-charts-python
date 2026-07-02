"""
StreamChart — a FastAPI + WebSocket backed chart that runs as a local HTTP server.

Usage::

    from lightweight_charts import StreamChart

    chart = StreamChart()
    chart.set(df)
    chart.show(port=8080, block=True)

    # asyncio: start the server and await until the port is accepting connections
    await chart.show_async(port=8080)

    # or start manually and await readiness
    chart.show(port=8080, block=False)
    await chart.ready()

The printed URL includes a one-time security token; share it only with trusted viewers.
"""

import asyncio
import os
import secrets
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .abstract import AbstractChart, Window
from .util import BulkRunScript, parse_event_message

# ---------------------------------------------------------------------------
# Module-level constant — must match the prefix used in abstract.Window
# ---------------------------------------------------------------------------
RETURN_PREFIX = "_~_~RETURN~_~_"

_JS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js")


class StreamWindow(Window):
    """
    Drop-in replacement for abstract.Window that communicates with a browser
    client over WebSocket instead of pywebview.

    Subclasses ``Window`` so ``_id_gen``, ``create_table``, ``style``, and
    other shared window helpers stay in sync with ``AbstractChart``.
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

        # Route batched JS through this window's WebSocket-aware run_script.
        self.bulk_run = BulkRunScript(self.run_script)

    @property
    def url(self) -> str | None:
        """HTTP URL for this stream window, set after :meth:`show`."""
        if self._host is None or self._port is None:
            return None
        return f"http://{self._host}:{self._port}/"

    @property
    def server_ready_event(self) -> threading.Event:
        """Set when the HTTP server is accepting connections on the bound port."""
        return self._server_ready

    @property
    def client_ready_event(self) -> threading.Event:
        """Set when a browser client has authenticated over WebSocket."""
        return self._client_ready

    def wait_server_ready(self, timeout: float | None = None) -> bool:
        """Block until the HTTP server is listening, or until *timeout* seconds."""
        return self._server_ready.wait(timeout=timeout)

    def wait_client_ready(self, timeout: float | None = None) -> bool:
        """Block until a browser client connects, or until *timeout* seconds."""
        return self._client_ready.wait(timeout=timeout)

    async def await_server_ready(self) -> None:
        """Await until the HTTP server is listening on the bound port."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._server_ready.wait)

    async def await_client_ready(self) -> None:
        """Await until a browser client has authenticated over WebSocket."""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._client_ready.wait)

    # ------------------------------------------------------------------
    # Public interface (mirrors abstract.Window)
    # ------------------------------------------------------------------

    def run_script(self, script: str, run_last: bool = False) -> None:
        """Send *script* to the connected browser, or buffer it for later."""
        if self.bulk_run.enabled:
            self.bulk_run.add_script(script)
            return
        if self._ws is not None and self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._ws.send_text(script), self._loop)
        else:
            self.scripts.append(script)

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

    def on_js_load(self, script: str) -> None:
        """
        Buffer *script* permanently (for replay on reconnect) and send it
        immediately if a client is already connected.
        """
        self.scripts.append(script)
        if self._ws is not None and self._loop is not None:
            asyncio.run_coroutine_threadsafe(self._ws.send_text(script), self._loop)

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
        wait_ready: bool = True,
    ) -> str:
        """Build the FastAPI app and start uvicorn in a daemon thread."""
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
                "Content-Security-Policy": ("default-src 'self'; script-src 'self' 'unsafe-eval'")
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
                print("WARNING: A second client attempted to connect; rejected with code 4002.")
                await websocket.close(code=4002)
                return

            self._ws = websocket

            # --- replay buffered scripts ---
            for script in list(self.scripts):
                await websocket.send_text(script)
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

        config = uvicorn.Config(app, host=host, port=port, log_level="error")
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
                    print(
                        f"ERROR: Port {port} is already in use. "
                        "Choose a different port with chart.show(port=<n>)."
                    )
                else:
                    raise

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        loop_ready.wait()  # ensure self._loop is set before returning
        if wait_ready and not self.wait_server_ready(timeout=30.0):
            raise TimeoutError(f"Timed out waiting for chart server to start on {host}:{port}")
        return self.url or f"http://{host}:{port}/"


class StreamChart(AbstractChart):
    """
    A chart served over HTTP/WebSocket.  Open the printed URL in any browser.

    ::

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

    @property
    def url(self) -> str | None:
        """HTTP URL for this chart, set after :meth:`show`."""
        return self.win.url

    @property
    def server_ready_event(self) -> threading.Event:
        """Set when the HTTP server is accepting connections on the bound port."""
        return self.win.server_ready_event

    @property
    def client_ready_event(self) -> threading.Event:
        """Set when a browser client has authenticated over WebSocket."""
        return self.win.client_ready_event

    def wait_ready(self, timeout: float | None = None) -> bool:
        """Block until the HTTP server is listening on the bound port."""
        return self.win.wait_server_ready(timeout=timeout)

    def wait_client(self, timeout: float | None = None) -> bool:
        """Block until a browser client connects over WebSocket."""
        return self.win.wait_client_ready(timeout=timeout)

    async def ready(self) -> None:
        """Await until the HTTP server is listening on the bound port."""
        await self.win.await_server_ready()

    async def client_ready(self) -> None:
        """Await until a browser client has authenticated over WebSocket."""
        await self.win.await_client_ready()

    def show(
        self,
        port: int = 8080,
        host: str = "127.0.0.1",
        open_browser: bool = False,
        block: bool = True,
        cors_origins: list[str] | None = None,
        wait_ready: bool = True,
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
        wait_ready:   Wait until the server is accepting connections before
                      returning (default True).
        """
        url = self.win.show(
            port=port,
            host=host,
            cors_origins=cors_origins,
            wait_ready=wait_ready,
        )
        print(f"Chart server running at {url} — press Ctrl+C to stop")

        if host not in ("127.0.0.1", "::1", "localhost"):
            print(
                "WARNING: Chart server is accessible from the network. "
                "Ensure the token URL is kept private."
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
    ) -> str:
        """
        Start the chart server, await readiness, and run until cancelled.

        Returns the chart URL once the server is accepting connections.
        Cancel the task or send ``KeyboardInterrupt`` to stop the server.
        """
        url = self.show(
            port=port,
            host=host,
            open_browser=open_browser,
            block=False,
            cors_origins=cors_origins,
            wait_ready=False,
        )
        await self.ready()
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            self.win.stop()
            return url
        except asyncio.CancelledError:
            self.win.stop()
            raise


async def wait_until_ready(
    chart: StreamChart,
    *,
    client: bool = False,
) -> None:
    """
    Await until a :class:`StreamChart` server (and optionally a browser client)
    is ready.

    Parameters
    ----------
    chart:    The chart instance returned by :class:`StreamChart`.
    client:   When ``True``, wait for a browser WebSocket connection instead
              of only the HTTP server.

    Use :func:`asyncio.timeout` to bound the wait::

        async with asyncio.timeout(5):
            await wait_until_ready(chart)
    """
    if client:
        await chart.client_ready()
    else:
        await chart.ready()
