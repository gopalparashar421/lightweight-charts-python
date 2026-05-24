"""test_toolbox.py -- drawing tests skipped in CI (require display)."""

import pytest


@pytest.mark.skip(reason="requires display: chart.show() + run_script_and_get()")
def test_create_horizontal_line(chart, bars):
    chart.set(bars)
    horz_line = chart.horizontal_line(200, width=4)
    chart.show()
    result = chart.win.run_script_and_get(f"{horz_line.id}._options")
    assert result
    chart.exit()


@pytest.mark.skip(reason="requires display: chart.show() + run_script_and_get()")
def test_create_trend_line(chart, bars):
    chart.set(bars)
    horz_line = chart.trend_line(bars.iloc[-10]["date"], 180, bars.iloc[-3]["date"], 190)
    chart.show()
    result = chart.win.run_script_and_get(f"{horz_line.id}._options")
    assert result
    chart.exit()


@pytest.mark.skip(reason="requires display: chart.show() + run_script_and_get()")
def test_create_box(chart, bars):
    chart.set(bars)
    box = chart.box(bars.iloc[-10]["date"], 180, bars.iloc[-3]["date"], 190)
    chart.show()
    result = chart.win.run_script_and_get(f"{box.id}._options")
    assert result
    chart.exit()


@pytest.mark.skip(reason="not yet implemented")
def test_create_vertical_line():
    pass


@pytest.mark.skip(reason="not yet implemented")
def test_create_vertical_span():
    pass
