import asyncio
import socket

import pytest

from lightweight_charts import StreamChart, wait_until_ready


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


@pytest.fixture
def stream_chart(bars):
    chart = StreamChart()
    chart.set(bars)
    yield chart
    chart.win.stop()


def test_show_returns_url_when_server_is_ready(stream_chart):
    port = _free_port()
    url = stream_chart.show(port=port, block=False)
    assert url == f"http://127.0.0.1:{port}/"
    assert stream_chart.url == url
    assert stream_chart.server_ready_event.is_set()
    assert _port_is_open("127.0.0.1", port)


@pytest.mark.anyio
async def test_ready_coroutine(stream_chart):
    port = _free_port()
    stream_chart.show(port=port, block=False, wait_ready=False)
    async with asyncio.timeout(5):
        await wait_until_ready(stream_chart)
    assert stream_chart.server_ready_event.is_set()
    assert stream_chart.url == f"http://127.0.0.1:{port}/"


@pytest.mark.anyio
async def test_show_async_starts_server(stream_chart):
    port = _free_port()
    task = asyncio.create_task(stream_chart.show_async(port=port))
    await asyncio.wait_for(stream_chart.ready(), timeout=5)
    assert stream_chart.url == f"http://127.0.0.1:{port}/"
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
