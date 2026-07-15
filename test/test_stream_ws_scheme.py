"""
Tests for StreamChart reverse-proxy / HTTPS support (QuantConsole plan 003).

Covers two fixes that live on fork branch ``v1.4``:

* ``stream-shim.js`` derives the WebSocket scheme from ``location.protocol``
  (``https:`` -> ``wss://``, else ``ws://``) instead of hardcoding ``ws://``.
* The ``/`` route emits an explicit ``connect-src 'self'`` CSP directive so a
  same-origin secure WebSocket is unambiguously allowed, while keeping
  ``default-src 'self'`` and ``script-src 'self' 'unsafe-eval'``.
"""

import socket
import urllib.request

import pytest

from lightweight_charts import StreamChart


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def running_stream(bars):
    chart = StreamChart()
    chart.set(bars)
    port = _free_port()
    chart.show(port=port, block=False)
    yield f"http://127.0.0.1:{port}"
    chart.win.stop()


def test_root_csp_allows_same_origin_websocket(running_stream):
    with urllib.request.urlopen(f"{running_stream}/", timeout=5) as resp:
        csp = resp.headers.get("Content-Security-Policy")
    assert csp is not None
    # Explicit same-origin WebSocket allowance (no longer implicit via default-src).
    assert "connect-src 'self'" in csp
    # Existing directives preserved.
    assert "default-src 'self'" in csp
    assert "script-src 'self' 'unsafe-eval'" in csp
    # Never widen to arbitrary third-party hosts / bare wss:.
    assert "wss:" not in csp


def test_shim_derives_scheme_from_location_protocol(running_stream):
    with urllib.request.urlopen(f"{running_stream}/stream-shim.js", timeout=5) as resp:
        shim = resp.read().decode()
    # No longer hardcodes the insecure scheme.
    assert "'ws://' + location.host" not in shim
    # Scheme is derived from the page protocol so HTTPS pages use wss://.
    assert "location.protocol" in shim
    assert "wss://" in shim
    assert "ws://" in shim
