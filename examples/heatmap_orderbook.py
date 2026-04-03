"""
Heatmap Series – Example 2: Orderbook Visualisation
=====================================================
Replicates the TypeScript bell-curve heatmap example using Python data
generation.  Each bar's heatmap cells are drawn from a bell curve centred on
the mid-price, simulating a depth-of-book (orderbook) heat map alongside a
price line.

Generation parameters match the original TS example:
  • 250 daily bars starting 2018-01-01
  • spread = 20 (price levels), binSize = 5
  • 10 000 Monte-Carlo samples per bar to build the histogram
  • Cell shader: purple gradient  rgba(155-a, 0, 155+a, 0.05 + a*0.01)
"""

import numpy as np
import pandas as pd
from lightweight_charts import Chart
from lightweight_charts.plugins import HeatmapSeries

# ── Reproducible seed ────────────────────────────────────────────────────────
np.random.seed(42)

# ── 1. Generate price line data (mirrors generateLineData in sample-data.ts) ─
N = 250
random_factor = 25 + np.random.rand() * 25


def _sample_point(i: int) -> float:
    return (
        i * (
            0.5
            + np.sin(i / 10) * 0.2
            + np.sin(i / 20) * 0.4
            + np.sin(i / random_factor) * 0.8
            + np.sin(i / 500) * 0.5
        )
        + 200
    )


dates = pd.date_range('2018-01-01', periods=N, freq='D')
prices = [_sample_point(i) for i in range(N)]
line_df = pd.DataFrame({'time': dates, 'Price': prices})


# ── 2. Bell-curve heatmap data (mirrors generateBellCurveHeatMapData) ────────
def _bell_curve_cells(
    center: float, spread: float = 20.0, bin_size: float = 5.0
) -> list[dict]:
    """Return heatmap cells for one bar using a bell-curve histogram."""
    samples = center + spread * np.random.randn(10_000)
    bins = np.floor(samples / bin_size) * bin_size
    unique_bins, counts = np.unique(bins, return_counts=True)
    # Add ±25 % jitter to match the original
    jitter = 1 + (np.random.rand(len(counts)) - 0.5) * 0.5
    amounts = counts * jitter
    return [
        {'low': float(b), 'high': float(b + bin_size), 'amount': float(a)}
        for b, a in zip(unique_bins, amounts)
    ]


rows: list[dict] = []
for ts, price in zip(dates, prices):
    for cell in _bell_curve_cells(price):
        rows.append({'time': ts, **cell})

heatmap_df = pd.DataFrame(rows)

# ── 3. Compute max amount (needed for normalising the cell shader) ───────────
max_amount = float(heatmap_df['amount'].max())

# ── 4. Purple-gradient cell shader (matches the TypeScript cellShader) ───────
cell_shader_js = f"""(amount) => {{
    const maxAmount = {max_amount};
    const amt = 100 * (amount / maxAmount);
    const r = Math.round(155 - amt);
    const g = 0;
    const b = Math.round(155 + amt);
    return `rgba(${{r}}, ${{g}}, ${{b}}, ${{(0.05 + amt * 0.010).toFixed(3)}})`;
}}"""

# ── 5. Build chart ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    chart = Chart()

    # Heatmap (orderbook depth) – no cell border to keep it clean
    heatmap = HeatmapSeries(
        chart,
        cell_shader_js=cell_shader_js,
        cell_border_width=0,
        pane_index=0,
    )
    heatmap.set(heatmap_df)

    # Price line on top of the heatmap
    line = chart.create_line(name='Price', color='black', width=1, pane_index=0)
    line.set(line_df)

    chart.fit()
    chart.show(block=True)
