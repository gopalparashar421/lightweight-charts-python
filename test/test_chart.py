import pandas as pd


def test_data_is_renamed(chart, bars):
    """_df_datetime_format normalises uppercase / mixed-case column names."""
    uppercase_df = pd.DataFrame(bars.copy()).rename(
        columns={
            "date": "Date",
            "open": "OPEN",
            "high": "HIgh",
            "low": "Low",
            "close": "close",
            "volume": "volUME",
        }
    )
    result = chart._df_datetime_format(uppercase_df)
    assert list(result.columns) == list(bars.rename(columns={"date": "time"}).columns)


def test_line_in_list(chart):
    """create_line() returns objects that appear in chart.lines() in order."""
    result0 = chart.create_line()
    result1 = chart.create_line()
    assert result0 == chart.lines()[0]
    assert result1 == chart.lines()[1]


def test_pane_returns_none(chart):
    """add_pane() does not return a value (returns None)."""
    result = chart.add_pane()
    assert result is None
