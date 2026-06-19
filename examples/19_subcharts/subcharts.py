import os

import pandas as pd

from lightweight_charts import Chart


def calculate_equity_curve(df):
    """Simulate a simple equity curve from close prices."""
    equity = (df["close"].pct_change().fillna(0) + 1).cumprod() * 100
    return pd.DataFrame({"time": df["date"], "Equity": equity})


if __name__ == "__main__":
    chart = Chart()
    chart.legend(visible=True)

    path = os.path.join(os.path.dirname(__file__), "ohlcv.csv")
    df = pd.read_csv(path)

    # Create a subchart tab — the tab bar appears automatically above
    equity_tab = chart.create_subchart(label="Equity Curve", main_label="Price")

    # Set OHLC data on the main (Price) chart
    chart.set(df)
    chart.watermark("Price")

    # Set equity curve on the second tab
    equity_data = calculate_equity_curve(df)
    equity_line = equity_tab.create_line("Equity")
    equity_line.set(equity_data)
    equity_tab.watermark("Equity Curve")

    chart.show(block=True)
