import asyncio
import inspect
import json
import logging
import multiprocessing as mp

import webview
from webview.errors import JavascriptException

from lightweight_charts import abstract

from .util import FLOAT, parse_event_message

logger = logging.getLogger(__name__)

_JS_ERROR_PREFIX = "__JS_ERROR__:"


def _emit_js_error(emit_queue, script: str, exc: Exception) -> None:
    """Forward a JS evaluation failure from the webview subprocess to the main process."""
    payload: dict = {"script": script, "error": str(exc)}
    try:
        msg = json.loads(str(exc))
        if isinstance(msg, dict):
            payload.update(
                name=msg.get("name"),
                line=msg.get("line"),
                column=msg.get("column"),
                message=msg.get("message"),
            )
    except (json.JSONDecodeError, TypeError):
        pass
    emit_queue.put(_JS_ERROR_PREFIX + json.dumps(payload))


def _log_js_error(payload: dict) -> None:
    script = payload.get("script", "")
    if len(script) > 500:
        script = script[:500] + "..."
    if payload.get("name") is not None:
        logger.error(
            "JavaScript error in script -> '%s': %s[%s:%s] %s",
            script,
            payload.get("name", "?"),
            payload.get("line", "?"),
            payload.get("column", "?"),
            payload.get("message") or payload.get("error", ""),
        )
    else:
        logger.error(
            "JavaScript error in script -> '%s': %s",
            script,
            payload.get("error", ""),
        )


class CallbackAPI:
    def __init__(self, emit_queue):
        self.emit_queue = emit_queue

    def callback(self, message: str):
        self.emit_queue.put(message)


class PyWV:
    def __init__(self, q, emit_q, return_q, loaded_event):
        self.queue = q
        self.return_queue = return_q
        self.emit_queue = emit_q
        self.loaded_event = loaded_event

        self.is_alive = True

        self.callback_api = CallbackAPI(emit_q)
        self.windows: list[webview.Window] = []
        self.loop()

    def create_window(
        self, width, height, x, y, screen=None, on_top=False, maximize=False, title=""
    ):
        screen = webview.screens[screen] if screen is not None else None
        if maximize:
            if screen is None:
                active_screen = webview.screens[0]
                width, height = active_screen.width, active_screen.height
            else:
                width, height = screen.width, screen.height

        self.windows.append(
            webview.create_window(
                title,
                url=abstract.INDEX,
                js_api=self.callback_api,
                width=width,
                height=height,
                x=x,
                y=y,
                screen=screen,
                on_top=on_top,
                background_color="#000000",
            )
        )

        self.windows[-1].events.loaded += lambda: self.loaded_event.set()

    def loop(self):
        # self.loaded_event.set()
        while self.is_alive:
            i, arg = self.queue.get()

            if i == "start":
                webview.start(debug=arg, func=self.loop)
                self.is_alive = False
                self.emit_queue.put("exit")
                return
            if i == "create_window":
                self.create_window(*arg)
                continue

            window = self.windows[i]
            if arg == "show":
                window.show()
            elif arg == "hide":
                window.hide()
            else:
                try:
                    if "_~_~RETURN~_~_" in arg:
                        self.return_queue.put(window.evaluate_js(arg[14:]))
                    else:
                        try:
                            # Uncomment these lines for debugging
                            # with open("script.js", "w") as f:
                            #    f.write(arg)

                            window.evaluate_js(arg)

                        except webview.errors.JavascriptException as e:
                            _emit_js_error(self.emit_queue, arg, e)
                except KeyError as e:
                    return e
                except JavascriptException as e:
                    _emit_js_error(self.emit_queue, arg, e)
                    msg = json.loads(str(e))
                    raise JavascriptException(
                        f"\n\nscript -> '{arg}',\nerror -> {msg['name']}[{msg['line']}:{msg['column']}]\n{msg['message']}"
                    )


class WebviewHandler:
    def __init__(self) -> None:
        self._reset()
        self.debug = False

    def _reset(self):
        self.loaded_event = mp.Event()
        self.return_queue = mp.Queue()
        self.function_call_queue = mp.Queue()
        self.emit_queue = mp.Queue()
        self.wv_process = mp.Process(
            target=PyWV,
            args=(
                self.function_call_queue,
                self.emit_queue,
                self.return_queue,
                self.loaded_event,
            ),
            daemon=True,
        )
        self.max_window_num = -1

    def create_window(
        self, width, height, x, y, screen=None, on_top=False, maximize=False, title=""
    ):
        self.function_call_queue.put(
            ("create_window", (width, height, x, y, screen, on_top, maximize, title))
        )
        self.max_window_num += 1
        return self.max_window_num

    def start(self):
        self.loaded_event.clear()
        self.wv_process.start()
        self.function_call_queue.put(("start", self.debug))
        self.loaded_event.wait()

    def show(self, window_num):
        self.function_call_queue.put((window_num, "show"))

    def hide(self, window_num):
        self.function_call_queue.put((window_num, "hide"))

    def evaluate_js(self, window_num, script):
        self.function_call_queue.put((window_num, script))

    def exit(self):
        if self.wv_process.is_alive():
            self.wv_process.terminate()
            self.wv_process.join()
        self._reset()


class Chart(abstract.AbstractChart):
    _main_window_handlers = None
    WV: WebviewHandler = WebviewHandler()

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        x: int | None = None,
        y: int | None = None,
        title: str = "",
        screen: int | None = None,
        on_top: bool = False,
        maximize: bool = False,
        debug: bool = False,
        toolbox: bool = False,
        inner_width: float = 1.0,
        inner_height: float = 1.0,
        scale_candles_only: bool = False,
        position: FLOAT = "left",
    ):
        Chart.WV.debug = debug
        self._i = Chart.WV.create_window(width, height, x, y, screen, on_top, maximize, title)

        window = abstract.Window(
            script_func=lambda s: Chart.WV.evaluate_js(self._i, s),
            js_api_code="pywebview.api.callback",
        )

        abstract.Window._return_q = Chart.WV.return_queue

        self.is_alive = True

        if Chart._main_window_handlers is None:
            super().__init__(
                window,
                inner_width,
                inner_height,
                scale_candles_only,
                toolbox,
                position=position,
            )
            Chart._main_window_handlers = self.win.handlers
        else:
            window.handlers = Chart._main_window_handlers
            super().__init__(
                window,
                inner_width,
                inner_height,
                scale_candles_only,
                toolbox,
                position=position,
            )

    def show(self, block: bool = False):
        """
        Shows the chart window.\n
        :param block: blocks execution until the chart is closed.
        """
        if not self.win.loaded:
            Chart.WV.start()
            Chart.WV.show(self._i)
            self.win.on_js_load()
        else:
            Chart.WV.show(self._i)
        if block:
            asyncio.run(self.show_async())

    async def show_async(self):
        self.show(block=False)
        try:
            from lightweight_charts import polygon

            [asyncio.create_task(self.polygon.async_set(*args)) for args in polygon._set_on_load]
            while 1:
                while Chart.WV.emit_queue.empty() and self.is_alive:
                    await asyncio.sleep(0.05)
                if not self.is_alive:
                    return
                response = Chart.WV.emit_queue.get()
                if response == "exit":
                    Chart.WV.exit()
                    self.is_alive = False
                    return
                if isinstance(response, str) and response.startswith(_JS_ERROR_PREFIX):
                    try:
                        _log_js_error(json.loads(response[len(_JS_ERROR_PREFIX) :]))
                    except (json.JSONDecodeError, TypeError):
                        logger.error(
                            "JavaScript error (malformed payload): %s",
                            response[:500],
                        )
                    continue
                func, args = parse_event_message(self.win, response)
                if func is None:
                    continue
                (await func(*args) if inspect.iscoroutinefunction(func) else func(*args))
        except KeyboardInterrupt:
            return

    def hide(self):
        """
        Hides the chart window.\n
        """
        self._q.put((self._i, "hide"))

    def exit(self):
        """
        Exits and destroys the chart window.\n
        """
        Chart.WV.exit()
        self.is_alive = False
