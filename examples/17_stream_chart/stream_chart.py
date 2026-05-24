"""
Stream Chart Example
====================

This script demonstrates StreamChart — a chart served over HTTP/WebSocket
so any browser can view it.

How to use
----------
1. Run this script:
       python examples/stream_chart.py

2. Open the printed URL in your browser, e.g.:
       http://127.0.0.1:8080/

Tips
----
- Pass `open_browser=True` to open the URL automatically during local dev:
      chart.show(port=8080, open_browser=True, block=True)

- To allow LAN / network access use host='0.0.0.0':
      chart.show(port=8080, host='0.0.0.0', block=True)
  WARNING: This exposes the server on your network.
"""

import pandas as pd
from lightweight_charts import StreamChart


def main():
    df = pd.read_csv("data.csv")

    chart = StreamChart()
    chart.set(df)
    chart.show(port=8080, block=True)


if __name__ == "__main__":
    main()
