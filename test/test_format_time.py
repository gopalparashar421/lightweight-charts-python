import pandas as pd


def _weekly_bars(bars):
    daily = bars.rename(columns={"date": "time"})
    daily["time"] = pd.to_datetime(daily["time"])
    return (
        daily.set_index("time")
        .resample("W")
        .agg(
            {
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
        .reset_index()
    )


def test_format_time_matches_set_data_on_weekly(chart, bars):
    weekly = _weekly_bars(bars)
    formatted = chart._df_datetime_format(weekly)

    for i in range(min(5, len(weekly))):
        bar_time = weekly["time"].iloc[i]
        stored = int(formatted.iloc[i]["time"])
        assert chart._format_time(bar_time, round=False) == stored
        assert chart._format_time(stored, round=False) == stored


def test_format_time_round_snaps_to_interval(chart, bars):
    weekly = _weekly_bars(bars)
    chart._df_datetime_format(weekly)

    bar_time = weekly["time"].iloc[0]
    stored = chart._format_time(bar_time, round=False)
    rounded = chart._format_time(bar_time, round=True)
    assert rounded != stored or chart._interval == 1
