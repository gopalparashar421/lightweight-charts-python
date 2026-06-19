# Subcharts (Tabs)

Tabbed subcharts let you switch between multiple independent charts inside a
single desktop window. Call `create_subchart()` on the main chart; a tab bar
appears automatically above the charts on the first call.

> **Note:** This is separate from the **Panes API** (`pane_index`, `add_pane()`),
> which stacks multiple series vertically in one chart view. See
> [`Pane` reference](../reference/pane.md) for multi-pane layouts.

___

## Price + Equity Curve

```python
import os

import pandas as pd

from lightweight_charts import Chart


def calculate_equity_curve(df):
  equity = (df["close"].pct_change().fillna(0) + 1).cumprod() * 100
  return pd.DataFrame({"time": df["date"], "Equity": equity})


if __name__ == "__main__":
  chart = Chart()
  chart.legend(visible=True)

  df = pd.read_csv("ohlcv.csv")

  # Tab bar appears on first call; main chart is labelled "Price"
  equity_tab = chart.create_subchart(label="Equity Curve", main_label="Price")

  chart.set(df)
  chart.watermark("Price")

  equity_line = equity_tab.create_line("Equity")
  equity_line.set(calculate_equity_curve(df))
  equity_tab.watermark("Equity Curve")

  chart.show(block=True)
```

Each tab is a full `SubChart` with the same API as `Chart` (`set`, `create_line`,
`topbar`, drawings, plugins, etc.).

___

## MACD in a Second Pane (single chart)

For indicators that share the same time axis but need a separate vertical pane,
use `pane_index` instead of tabs:

```python
import pandas as pd
from lightweight_charts import Chart


def calculate_macd(df, short=12, long=26, signal=9):
  short_ema = df["close"].ewm(span=short, adjust=False).mean()
  long_ema = df["close"].ewm(span=long, adjust=False).mean()
  macd = short_ema - long_ema
  sig = macd.ewm(span=signal, adjust=False).mean()
  return pd.DataFrame({
    "time": df["date"],
    "MACD": macd,
    "Signal": sig,
    "Histogram": macd - sig,
  }).dropna()


if __name__ == "__main__":
  chart = Chart(inner_height=1)
  chart.legend(visible=True)

  df = pd.read_csv("ohlcv.csv")
  chart.set(df)

  macd_data = calculate_macd(df)
  histogram = chart.create_histogram("MACD", pane_index=1)
  histogram.set(macd_data[["time", "MACD", "Signal", "Histogram"]])
  chart.legend(visible=True, pane_index=1)

  chart.show(block=True)
```
