"""
Tests for StreamChart reconnect snapshot fix (Plan 013).

Covers: bounded structural buffer, transient tagging, candlestick OHLC snapshot
(H-01), atomic cutover (H-02), bulk_run tagging (M-01), buffer content (L-03),
and stream-shim reload hardening (M-03).
"""

from __future__ import annotations

import socket
import threading
import time
import urllib.request
from contextlib import nullcontext

import pandas as pd
import pytest

from lightweight_charts import StreamChart
from lightweight_charts.abstract import Window
from lightweight_charts.stream import StreamWindow


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _make_bar(t: int, price: float = 100.0) -> pd.Series:
    return pd.Series(
        {
            "time": t,
            "open": price,
            "high": price + 1,
            "low": price - 1,
            "close": price + 0.5,
            "volume": 1000.0,
        }
    )


@pytest.fixture
def disconnected_stream(bars):
    """StreamChart with initial data set, no client connected."""
    chart = StreamChart()
    chart.set(bars)
    yield chart
    chart.win.stop()


# ---------------------------------------------------------------------------
# Milestone 1 — seams on base Window
# ---------------------------------------------------------------------------


def test_window_run_script_accepts_transient_kwarg():
    """Base Window accepts transient= and ignores it (no TypeError)."""
    calls = []
    win = Window(script_func=calls.append)
    win.loaded = True
    win.run_script("1+1", transient=True)
    assert calls == ["1+1"]


def test_window_data_guard_is_nullcontext():
    win = Window(script_func=lambda s: None)
    guard = win.data_guard()
    assert isinstance(guard, nullcontext) or type(guard).__name__ == "_GeneratorContextManager"
    with win.data_guard():
        pass


# ---------------------------------------------------------------------------
# Milestone 3 — bounded buffer while disconnected
# ---------------------------------------------------------------------------


def test_update_while_disconnected_keeps_script_buffer_stable(disconnected_stream, bars):
    chart = disconnected_stream
    win = chart.win
    baseline = len(win.scripts)

    start_t = int(chart.candle_data.iloc[-1]["time"])
    for i in range(50):
        chart.update(_make_bar(start_t + (i + 1) * 60, 100 + i))

    assert len(win.scripts) == baseline


def test_structural_scripts_retained_transient_absent(disconnected_stream, bars):
    chart = disconnected_stream
    win = chart.win
    start_t = int(chart.candle_data.iloc[-1]["time"])
    for i in range(20):
        chart.update(_make_bar(start_t + (i + 1) * 60, 100 + i))

    joined = "\n".join(win.scripts)
    assert "new Lib.Handler" in joined or "Lib.Handler" in joined
    assert ".series.update(" not in joined
    assert ".setData(" not in joined
    assert ".seriesMarkers." not in joined


def test_bulk_run_updates_while_disconnected_keep_buffer_stable(disconnected_stream):
    chart = disconnected_stream
    win = chart.win
    baseline = len(win.scripts)
    start_t = int(chart.candle_data.iloc[-1]["time"])

    with win.bulk_run:
        for i in range(30):
            chart.update(_make_bar(start_t + (i + 1) * 60, 100 + i))

    assert len(win.scripts) == baseline


# ---------------------------------------------------------------------------
# Milestone 2 — snapshot emitters (H-01)
# ---------------------------------------------------------------------------


def test_candlestick_snapshot_emits_ohlc_not_empty(disconnected_stream):
    chart = disconnected_stream
    scripts = chart.data_snapshot_scripts()
    joined = "\n".join(scripts)

    assert f"{chart.id}.series.setData(" in joined
    # Must not be empty array — OHLC records present
    assert f"{chart.id}.series.setData([])" not in joined
    assert '"open"' in joined or "'open'" in joined or "open" in joined
    assert "volumeSeries.setData(" in joined
    # No structural side effects
    assert "clearDrawings" not in joined
    assert "autoScale" not in joined


def test_series_snapshot_empty_when_no_data():
    chart = StreamChart()
    try:
        line = chart.create_line("sma")
        assert line.data_snapshot_scripts() == []
    finally:
        chart.win.stop()


def test_marker_snapshot_included(disconnected_stream, bars):
    chart = disconnected_stream
    t = chart.candle_data.iloc[0]["time"]
    chart.marker(time=t, shape="circle", color="#2196F3", text="x")
    scripts = chart.data_snapshot_scripts()
    joined = "\n".join(scripts)
    assert "seriesMarkers.setMarkers" in joined


# ---------------------------------------------------------------------------
# Milestone 3 — connect handshake via WebSocket
# ---------------------------------------------------------------------------


def test_connect_payload_bounded_not_proportional_to_updates(bars):
    chart = StreamChart()
    chart.set(bars)
    start_t = int(chart.candle_data.iloc[-1]["time"])
    n_updates = 80
    for i in range(n_updates):
        chart.update(_make_bar(start_t + (i + 1) * 60, 100 + i))

    port = _free_port()
    chart.show(port=port, block=False)
    try:
        try:
            import websockets.sync.client as ws_sync
        except ImportError:
            pytest.skip("websockets sync client not available")

        uri = f"ws://127.0.0.1:{port}/ws"
        with ws_sync.connect(uri) as ws:
            ws.send(chart.win.token)
            messages = []
            # Drain until idle briefly
            deadline = time.time() + 3.0
            while time.time() < deadline:
                try:
                    msg = ws.recv(timeout=0.3)
                    messages.append(msg)
                except TimeoutError:
                    break
                except Exception:
                    break

        # Must be far fewer than n_updates (snapshot, not per-bar replay)
        assert len(messages) < n_updates, (
            f"expected snapshot-sized payload, got {len(messages)} msgs for {n_updates} updates"
        )
        joined = "\n".join(messages)
        assert ".series.setData(" in joined
        assert "open" in joined
    finally:
        chart.win.stop()


def test_auth_4001_and_guard_4002_still_work(bars):
    chart = StreamChart()
    chart.set(bars)
    port = _free_port()
    chart.show(port=port, block=False)
    try:
        try:
            import websockets.sync.client as ws_sync
            from websockets.exceptions import ConnectionClosed
        except ImportError:
            pytest.skip("websockets sync client not available")

        uri = f"ws://127.0.0.1:{port}/ws"

        # Bad token → 4001
        with ws_sync.connect(uri) as ws:
            ws.send("not-the-token")
            with pytest.raises(ConnectionClosed) as exc_info:
                ws.recv(timeout=2)
            assert exc_info.value.code == 4001

        # First client OK
        ws1 = ws_sync.connect(uri)
        ws1.send(chart.win.token)
        # drain a bit
        try:
            ws1.recv(timeout=0.5)
        except TimeoutError:
            pass

        # Second client → 4002
        with ws_sync.connect(uri) as ws2:
            ws2.send(chart.win.token)
            with pytest.raises(ConnectionClosed) as exc_info2:
                ws2.recv(timeout=2)
            assert exc_info2.value.code == 4002

        ws1.close()
    finally:
        chart.win.stop()


def test_stream_during_connect_does_not_drop_bars(bars):
    """H-02: updates during handshake must not leave a permanent gap."""
    chart = StreamChart()
    chart.set(bars)
    start_t = int(chart.candle_data.iloc[-1]["time"])
    port = _free_port()
    chart.show(port=port, block=False)

    try:
        try:
            import websockets.sync.client as ws_sync
        except ImportError:
            pytest.skip("websockets sync client not available")

        # Wait until the port accepts TCP connections (server_ready can race briefly).
        deadline = time.time() + 5.0
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.2)
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.05)
        else:
            pytest.fail(f"server did not accept connections on {port}")

        barrier = threading.Barrier(2)
        errors: list[str] = []

        def streamer():
            try:
                barrier.wait(timeout=5)
                for i in range(20):
                    chart.update(_make_bar(start_t + (i + 1) * 60, 200 + i))
                    time.sleep(0.01)
            except Exception as e:
                errors.append(str(e))

        t = threading.Thread(target=streamer, daemon=True)
        t.start()

        uri = f"ws://127.0.0.1:{port}/ws"
        with ws_sync.connect(uri) as ws:
            barrier.wait(timeout=5)
            ws.send(chart.win.token)
            messages = []
            deadline = time.time() + 4.0
            while time.time() < deadline:
                try:
                    msg = ws.recv(timeout=0.2)
                    messages.append(msg)
                except TimeoutError:
                    if not t.is_alive():
                        try:
                            while True:
                                messages.append(ws.recv(timeout=0.15))
                        except TimeoutError:
                            break
                        break
                    continue

        t.join(timeout=5)
        assert not errors, errors

        expected_last = start_t + 20 * 60
        assert int(chart.candle_data.iloc[-1]["time"]) == expected_last

        joined = "\n".join(messages)
        assert str(expected_last) in joined or str(float(expected_last)) in joined
    finally:
        chart.win.stop()


# ---------------------------------------------------------------------------
# Milestone 4 — stream-shim.js hardening
# ---------------------------------------------------------------------------


def test_shim_reload_on_established_close_and_4002_hardening(bars):
    chart = StreamChart()
    chart.set(bars)
    port = _free_port()
    chart.show(port=port, block=False)
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/stream-shim.js", timeout=5) as resp:
            shim = resp.read().decode()
        # Scheme derivation preserved
        assert "location.protocol" in shim
        assert "wss://" in shim
        assert "ws://" in shim
        assert "'ws://' + location.host" not in shim
        # Token send preserved
        assert "ws.send(token)" in shim or "ws.send(" in shim
        # Reload on established close
        assert "location.reload" in shim
        # 4002 hardening
        assert "4002" in shim
    finally:
        chart.win.stop()


def test_stream_window_data_guard_is_real_lock():
    win = StreamWindow()
    assert hasattr(win, "data_guard")
    with win.data_guard():
        acquired = threading.Event()
        released = threading.Event()

        def other():
            with win.data_guard():
                acquired.set()
            released.set()

        t = threading.Thread(target=other)
        t.start()
        time.sleep(0.05)
        assert not acquired.is_set()
    t.join(timeout=2)
    assert acquired.is_set()
    assert released.is_set()
