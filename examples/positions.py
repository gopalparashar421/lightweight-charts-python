"""
positions.py
============

Demonstrates the PositionTool plugin:
  - Creating a LONG risk/reward overlay on a candlestick chart.
  - The right edge auto-tracks every new incoming bar.
  - Mid-trade: stop is trailed to break-even once price is in profit.
  - The overlay is removed when the take-profit price is reached.

Data: Tesla (TSLA) daily OHLCV, March 2023.
"""

import os
import pandas as pd
from time import sleep
from lightweight_charts import Chart, PositionTool

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
CSV  = os.path.join(HERE, '1_setting_data', 'ohlcv.csv')

# ── Config ────────────────────────────────────────────────────────────────────
ENTRY_IDX      = 2960          # bar index used as "entry" bar
ENTRY_PRICE    = 183.86
STOP_PRICE     = 175.00        # below the recent swing low
TARGET_PRICE   = 202.00        # ~1 : 2  R:R
BE_TRIGGER     = 192.00        # move stop to break-even above this price
ACCOUNT_BAL    = 10_000.00     # USD
RISK_PCT       = 1.5           # 1.5 % of account per trade
STREAM_DELAY   = 10          # seconds between streamed candles

if __name__ == '__main__':
    df = pd.read_csv(CSV, index_col=0)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={'date': 'time'})
    df['time'] = pd.to_datetime(df['time'])

    # Split: everything up-to-and-including the entry bar is "historical"
    history   = df.iloc[:ENTRY_IDX + 1].copy()
    live_feed = df.iloc[ENTRY_IDX + 1:].copy()

    # ── Build chart ───────────────────────────────────────────────────────────
    chart = Chart(title='PositionTool demo – TSLA daily')
    chart.candle_style(
        up_color='#26a69a', down_color='#ef5350',
        wick_up_color='#26a69a', wick_down_color='#ef5350',
    )
    chart.set(history)
    chart.fit()

    # ── Create long position ──────────────────────────────────────────────────
    entry_bar  = history.iloc[-1]
    entry_time = entry_bar['time']

    position = PositionTool(
        series         = chart,
        entry          = ENTRY_PRICE,
        stop           = STOP_PRICE,
        target         = TARGET_PRICE,
        entry_time     = entry_time,
        # endTime omitted → auto-tracks the latest bar
        account_balance = ACCOUNT_BAL,
        risk_percent    = RISK_PCT,
    )

    chart.show()

    # ── Stream live bars ──────────────────────────────────────────────────────
    stop_moved_to_be = False

    for _, bar in live_feed.iterrows():
        close = bar['close']
        chart.update(bar)

        # Trail stop to break-even once price is sufficiently in profit
        if not stop_moved_to_be and close >= BE_TRIGGER:
            position.update(stop=round(ENTRY_PRICE, 2))
            stop_moved_to_be = True

        # Remove the overlay when target is hit
        if close >= TARGET_PRICE:
            position.delete()
            break

        sleep(STREAM_DELAY)
