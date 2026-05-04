"""
positions.py
============

Demonstrates the PositionTool plugin via the marker-like API:
  - ``position_list()`` to set multiple historical positions at once.
  - ``position()`` to add a single live position and get back an id.
  - ``remove_position(id)`` to delete an overlay when it is no longer needed.

Two historical positions are loaded via ``position_list()``.
A third (live) position is opened with ``position()`` as bars stream in.
The live overlay is removed when the take-profit price is reached.

Data: Tesla (TSLA) daily OHLCV, March 2023.
"""

import pandas as pd
from time import sleep
from lightweight_charts import Chart

# ── Config ────────────────────────────────────────────────────────────────────
ENTRY_IDX    = 1700         # bar index used as the live entry bar
ENTRY_PRICE  = 2360.00
STOP_PRICE   = 2390.00      # short position: stop above entry
TARGET_PRICE = 2335.00      # short target below entry  (~1:2 R:R)
STREAM_DELAY = 0            # seconds between streamed candles

if __name__ == '__main__':
    df = pd.read_csv('data.csv')

    # Split: everything up-to-and-including the entry bar is "historical"
    history   = df.iloc[:ENTRY_IDX + 1].copy()
    live_feed = df.iloc[ENTRY_IDX + 1:].copy()

    # ── Build chart ───────────────────────────────────────────────────────────
    chart = Chart(title='PositionTool demo - TSLA daily')
    chart.candle_style(
        up_color='#26a69a', down_color='#ef5350',
        wick_up_color='#26a69a', wick_down_color='#ef5350',
    )
    chart.set(history)
    chart.fit()

    # ── Historical positions via position_list() ──────────────────────────────
    hist_ids = chart.position_list([
        {
            'entry':      2100.00,
            'stop':       2050.00,
            'target':     2200.00,
            'entry_time': df.iloc[1600]['time'],
            'end_time':   df.iloc[1650]['time'],    # pinned right edge
        },
        {
            'entry':        2250.00,
            'stop':         2300.00,
            'target':       2150.00,
            'entry_time':   df.iloc[1650]['time'],
            'end_time':     df.iloc[1690]['time'],
            'stop_color':   'rgba(239, 83, 80, 0.15)',
            'target_color': 'rgba(38, 166, 154, 0.15)',
        },
    ])

    # ── Live position via position() ──────────────────────────────────────────
    entry_time = history.iloc[-1]['time']
    live_id = chart.position(
        entry=ENTRY_PRICE,
        stop=STOP_PRICE,
        target=TARGET_PRICE,
        entry_time=entry_time,
        # end_time omitted - auto-tracks the latest bar
    )

    chart.show(block=False)

    # ── Stream live bars ──────────────────────────────────────────────────────
    for _, bar in live_feed.iterrows():
        close = bar['close']
        chart.update(bar)

        # Remove the live overlay when target is reached
        if close <= TARGET_PRICE and live_id in chart.positions:
            chart.remove_position(live_id)

        sleep(STREAM_DELAY)

    chart.show(block=True)
