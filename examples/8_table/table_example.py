import os
import pandas as pd
from lightweight_charts import Chart

"""
Table Example
=============
Demonstrates the full Table API:
  - Creating a table with custom widths, alignments, and colors
  - Adding rows with new_row()
  - Styling cells with background_color() and text_color()
  - Using format() to apply value templates
  - Header and footer sections
  - Row click callbacks to sync chart data
  - Updating cell values dynamically
  - Toggling table visibility
"""

HEADINGS = ('Symbol', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change %')

# Per-symbol OHLCV slices (last 5 bars shown in chart on click)
SYMBOLS = {
    'TSLA': {'color': '#e8a838'},
    'AAPL': {'color': '#00bcd4'},
    'AMZN': {'color': '#ab47bc'},
}

# Simulated summary rows (in production these would come from real data)
SUMMARY = [
    ('TSLA', 180.25, 185.60, 178.90, 183.40, 52_341_200, 1.75),
    ('AAPL', 170.10, 172.85, 169.30, 171.95, 64_128_900, 1.09),
    ('AMZN', 178.90, 181.20, 177.55, 180.10, 38_762_400, 0.67),
]


def on_row_click(row):
    """Called when a table row is clicked — highlight it and load chart data."""
    # Reset all row header colors
    for r in table.values():
        r.background_color('Symbol', '#121417')
        r.text_color('Symbol', '#d8d9db')

    # Highlight clicked row
    symbol = row['Symbol']
    color = SYMBOLS[symbol]['color']
    row.background_color('Symbol', color)
    row.text_color('Symbol', '#000000')

    # Update chart with a filtered view of the dataset
    filtered = df[df['close'] > 0].tail(60)  # last 60 bars as illustration
    chart.topbar['symbol'].set(symbol)
    chart.set(filtered)


def color_change_cell(row, change_pct):
    """Apply green/red coloring to the Change % cell."""
    color = '#26a69a' if change_pct >= 0 else '#ef5350'
    row.background_color('Change %', color)
    row.text_color('Change %', '#ffffff')


if __name__ == '__main__':
    chart = Chart(toolbox=False)
    chart.legend(visible=True)

    # Load sample data
    path = os.path.join(os.path.dirname(__file__), 'ohlcv.csv')
    df = pd.read_csv(path)
    chart.set(df)

    # Add a symbol label to the top bar
    chart.topbar.textbox('symbol', 'TSLA')

    # ── Create the table ────────────────────────────────────────────────────
    table = chart.create_table(
        width=0.35,
        height=0.35,
        headings=HEADINGS,
        widths=(0.20, 0.13, 0.13, 0.13, 0.13, 0.15, 0.13),
        alignments=('left', 'right', 'right', 'right', 'right', 'right', 'right'),
        position='left',
        draggable=True,
        background_color='#131722',
        border_color='rgb(50, 56, 68)',
        border_width=1,
        heading_text_colors=('#9598a1',) * len(HEADINGS),
        heading_background_colors=('#1e222d',) * len(HEADINGS),
        func=on_row_click,
    )

    # Apply a "$ " prefix formatter to price columns
    for col in ('Open', 'High', 'Low', 'Close'):
        table.format(col, f'$ {table.VALUE}')

    # Apply a volume formatter with commas (formatted on the Python side)
    # and a "%" suffix for the change column
    table.format('Change %', f'{table.VALUE} %')

    # ── Add a header section with a title ───────────────────────────────────
    table.header(1)
    table.header[0] = 'Market Overview'

    # ── Populate rows ───────────────────────────────────────────────────────
    for sym, o, h, l, c, vol, chg in SUMMARY:
        row = table.new_row(
            sym,
            round(o, 2),
            round(h, 2),
            round(l, 2),
            round(c, 2),
            f'{vol:,.0f}',
            round(chg, 2),
        )
        color_change_cell(row, chg)

    # Highlight the first row (TSLA) as the default selection
    first_row = list(table.values())[0]
    first_row.background_color('Symbol', SYMBOLS['TSLA']['color'])
    first_row.text_color('Symbol', '#000000')

    # ── Add a footer with a note ─────────────────────────────────────────────
    table.footer(1)
    table.footer[0] = 'Click a row to load symbol data'

    chart.show(block=True)
