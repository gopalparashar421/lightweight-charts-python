"""test_bands_indicator.py — unit tests for BandsIndicator DataFrame API."""

import pandas as pd
import pytest

from lightweight_charts.plugins import BandsIndicator


@pytest.fixture
def band_frames():
    """Minimal upper/lower DataFrames with time + value columns."""
    dates = pd.date_range("2024-01-01", periods=10, freq="1h")
    upper = pd.DataFrame({"time": dates, "value": [102.0 + i * 0.1 for i in range(10)]})
    lower = pd.DataFrame({"time": dates, "value": [98.0 - i * 0.1 for i in range(10)]})
    return upper, lower


def test_bands_constructs_with_dataframes(chart, band_frames):
    """BandsIndicator(chart, upper_df, lower_df) must construct without error."""
    upper_df, lower_df = band_frames
    bands = BandsIndicator(chart, upper_df, lower_df)
    assert bands is not None


def test_bands_creates_two_internal_lines(chart, band_frames):
    """BandsIndicator must register exactly two hidden Lines on the chart."""
    upper_df, lower_df = band_frames
    initial_count = len(chart.lines())
    BandsIndicator(chart, upper_df, lower_df)
    assert len(chart.lines()) == initial_count + 2


def test_bands_internal_lines_are_accessible(chart, band_frames):
    """Internal _upper_line and _lower_line attributes must exist after construction."""
    upper_df, lower_df = band_frames
    bands = BandsIndicator(chart, upper_df, lower_df)
    assert hasattr(bands, "_upper_line")
    assert hasattr(bands, "_lower_line")


def test_bands_delete_removes_internal_lines(chart, band_frames):
    """delete() must remove both internal Lines from chart.lines()."""
    upper_df, lower_df = band_frames
    initial_count = len(chart.lines())
    bands = BandsIndicator(chart, upper_df, lower_df)
    assert len(chart.lines()) == initial_count + 2
    bands.delete()
    assert len(chart.lines()) == initial_count


def test_bands_rejects_old_series_signature(chart):
    """Passing a SeriesCommon as first positional arg must raise TypeError — no compat shim."""
    line = chart.create_line()
    with pytest.raises(TypeError):
        BandsIndicator(line, line)  # old interface — must fail
