"""Tests for shape text label options emitted to JS."""

import pytest


def _scripts_after(chart, call):
    start = len(chart.win.scripts)
    call()
    return "".join(chart.win.scripts[start:])


@pytest.fixture
def chart_with_data(chart, bars):
    chart.set(bars)
    return chart, bars


def test_horizontal_line_text_options(chart_with_data):
    chart, _ = chart_with_data
    scripts = _scripts_after(
        chart,
        lambda: chart.horizontal_line(
            200,
            text="Resistance",
            text_position="below",
            axis_label_visible=False,
            text_color="#ff0000",
        ),
    )
    assert "text: `Resistance`" in scripts
    assert "textPosition: 'below'" in scripts
    assert "axisLabelVisible: false" in scripts
    assert 'textColor: "#ff0000"' in scripts or "textColor: '#ff0000'" in scripts


def test_vertical_line_text_options(chart_with_data):
    chart, bars = chart_with_data
    scripts = _scripts_after(
        chart,
        lambda: chart.vertical_line(
            bars.iloc[-1]["date"],
            text="Event",
            text_h_align="right",
            text_v_align="top",
        ),
    )
    assert "text: `Event`" in scripts
    assert "textHAlign: 'right'" in scripts
    assert "textVAlign: 'top'" in scripts


def test_box_text_options(chart_with_data):
    chart, bars = chart_with_data
    scripts = _scripts_after(
        chart,
        lambda: chart.box(
            bars.iloc[-10]["date"],
            180,
            bars.iloc[-3]["date"],
            190,
            text="Zone",
            text_position="left",
        ),
    )
    assert "text: `Zone`" in scripts
    assert 'textPosition: "left"' in scripts


def test_trend_line_text_options(chart_with_data):
    chart, bars = chart_with_data
    scripts = _scripts_after(
        chart,
        lambda: chart.trend_line(
            bars.iloc[-10]["date"],
            180,
            bars.iloc[-3]["date"],
            190,
            text="Trend",
            text_position="end",
        ),
    )
    assert "text: `Trend`" in scripts
    assert 'textPosition: "end"' in scripts


def test_ray_line_text_options(chart_with_data):
    chart, bars = chart_with_data
    scripts = _scripts_after(
        chart,
        lambda: chart.ray_line(
            bars.iloc[-10]["date"],
            185,
            text="Ray",
            text_position="above",
            axis_label_visible=False,
        ),
    )
    assert "text: `Ray`" in scripts
    assert "textPosition: 'above'" in scripts
    assert "axisLabelVisible: false" in scripts
