"""
Heatmap Series – Orderbook Visualisation
=========================================
Demonstrates feeding orderbook (bid/ask) data into a HeatmapSeries with
per-side amount-based shaders:

  - Bid cells: green gradient (dim at low size, bright at high size)
  - Ask cells: red gradient   (dim at low size, bright at high size)

``heatmap.set(time, bids, asks)``    – replace all data with one snapshot
``heatmap.update(time, bids, asks)`` – append / update a bar

The simulated feed uses 100 hourly bars.  Each bar has 10 bid levels below the
mid-price and 10 ask levels above it, with random sizes (1–300 contracts).
Sizes are normalised inside the shader so the brightest cell has the most liquidity.
"""

import numpy as np
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import HeatmapSeries

# ── Reproducible seed ────────────────────────────────────────────────────────
np.random.seed(42)

# ── 1. Simulate a price series ───────────────────────────────────────────────
N = 100
dates = pd.date_range('2024-01-01', periods=N, freq='h')
prices = 100.0 + np.cumsum(np.random.randn(N) * 0.5)

# ── 2. Helper: build a synthetic orderbook around a mid price ────────────────
DEPTH = 10    # price levels on each side
TICK  = 0.5   # spacing between levels
MAX_SIZE = 300


def make_orderbook(mid: float) -> tuple[list, list]:
    """Return (bids, asks) as list[tuple[str, int]] for a given mid price."""
    bids = [
        (str(round(mid - (i + 1) * TICK, 2)), int(np.random.randint(1, MAX_SIZE)))
        for i in range(DEPTH)
    ]
    asks = [
        (str(round(mid + (i + 1) * TICK, 2)), int(np.random.randint(1, MAX_SIZE)))
        for i in range(DEPTH)
    ]
    return bids, asks


# ── 3. Per-side shaders ───────────────────────────────────────────────────────
# Each shader receives the raw ``amount`` value and returns a CSS color string.
# Normalise against MAX_SIZE so color intensity is comparable across bars.

bid_shader_js = f"""(amount) => {{
    const t = Math.min(amount / {MAX_SIZE}, 1);
    const g = Math.round(80 + t * 175);   // 80 -> 255
    const a = (0.15 + t * 0.85).toFixed(2);
    return `rgba(0, ${{g}}, 60, ${{a}})`;
}}"""

ask_shader_js = f"""(amount) => {{
    const t = Math.min(amount / {MAX_SIZE}, 1);
    const r = Math.round(80 + t * 175);   // 80 -> 255
    const a = (0.15 + t * 0.85).toFixed(2);
    return `rgba(${{r}}, 30, 30, ${{a}})`;
}}"""

# ── 4. Build chart ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    chart = Chart()

    heatmap = HeatmapSeries(
        chart,
        cell_border_width=0,
        bid_shader_js=bid_shader_js,
        ask_shader_js=ask_shader_js,
        pane_index=0,
    )

    # Load the first snapshot with set() – replaces all existing data
    first_bids, first_asks = make_orderbook(prices[0])
    heatmap.set(dates[0], first_bids, first_asks)

    # Stream the remaining snapshots with update() – appends each bar
    for date, price in zip(dates[1:], prices[1:]):
        bids, asks = make_orderbook(price)
        heatmap.update(date, bids, asks)

    # Price line on top of the heatmap
    line = chart.create_line(name='Price', color='white', width=2, pane_index=0)
    line.set(pd.DataFrame({'time': dates, 'Price': prices}))

    chart.fit()
    chart.show(block=True)
