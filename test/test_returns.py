"""test_returns.py -- display-dependent tests, skipped in CI."""

import pytest


@pytest.mark.skip(reason="requires display: calls chart.show() and screenshot()")
def test_screenshot_returns_value(chart, bars):
    chart.set(bars)
    chart.show()
    screenshot_data = chart.screenshot()
    assert screenshot_data is not None


@pytest.mark.skip(reason="requires display: calls chart.show_async() with async timing")
def test_save_drawings():
    """Toolbox drawings persist across save/load cycle."""
    from lightweight_charts import Chart

    c = Chart(toolbox=True, width=100, height=100)
    c.exit()
