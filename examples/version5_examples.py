import pandas as pd
from time import sleep
from lightweight_charts import Chart

if __name__ == '__main__':
    chart = Chart(inner_height=1, debug=True)
    chart.layout(background_color='#090c0e', text_color='#FFFFFF')

    df = pd.read_csv('data.csv')
    chart.set(df)
    chart.legend(visible=True, ohlc=True, percent=True, lines=True)

    # ── Pane 0: candlestick + KAMA overlays ──────────────────────────────────
    kama10 = chart.create_line('KAMA_10_2_5',  color='#E91E63', pane_index=0)
    kama10.set(df[['time', 'KAMA_10_2_5']])

    kama20 = chart.create_line('KAMA_20_2_10', color='#2196F3', pane_index=0)
    kama20.set(df[['time', 'KAMA_20_2_10']])

    # ── Pane 1: ADX / directional movement ───────────────────────────────────
    chart.add_pane()
    adx  = chart.create_line('ADX_10',    color='#FFD700', pane_index=1)
    adxr = chart.create_line('ADXR_10_2', color='#FF6B35', pane_index=1)
    dmp  = chart.create_line('DMP_10',    color='#4CAF50', pane_index=1)
    dmn  = chart.create_line('DMN_10',    color='#F44336', pane_index=1)
    adx.set(df[['time', 'ADX_10']])
    adxr.set(df[['time', 'ADXR_10_2']])
    dmp.set(df[['time', 'DMP_10']])
    dmn.set(df[['time', 'DMN_10']])
    adx.legend(visible=True)
    # ── Pane 2: RSI ───────────────────────────────────────────────────────────
    chart.add_pane()
    rsi = chart.create_area('ULT_RSI_10', line_color='#9C27B0', pane_index=2)
    rsi.set(df[['time', 'ULT_RSI_10']])
    rsi.legend(visible=True)
    # ── Pane 3: Bollinger %B ─────────────────────────────────────────────────
    chart.add_pane()
    bbp = chart.create_line('BBP_20_2.0_2.0', color='#00BCD4', pane_index=3)
    bbp.set(df[['time', 'BBP_20_2.0_2.0']])
    bbp.legend(visible=True)
    # ── Callbacks ─────────────────────────────────────────────────────────────
    def on_dbl_click(c, time, price):
        print(f"[DblClick] time={time}, price={price:.4f}")

    chart.subscribe_dbl_click(on_dbl_click)

    def on_data_changed(s):
        print(f"[DataChanged] series: {s.name}")

    kama10.subscribe_data_changed(on_data_changed)

    # ── Table (tests row-click and cell-click error) ───────────────────────────
    def on_row_click(row, cell=None):
        if cell is not None:
            print(f"[TableClick] row={dict(row)!r}  cell={cell!r}")
        else:
            print(f"[TableClick] row={dict(row)!r}")

    table = chart.create_table(
        width=220, height=160,
        headings=('Symbol', 'Price', 'Chg'),
        widths=(0.4, 0.3, 0.3),
        alignments=('left', 'right', 'right'),
        position='right',
        draggable=True,
        return_clicked_cells=True,
    )
    btc_row = table.new_row('BTC', '95000', '+1.2%')
    eth_row = table.new_row('ETH', '3500',  '-0.5%')
    sol_row = table.new_row('SOL', '180',   '+3.1%')
    btc_row.background_color('Chg', 'rgba(76,175,80,0.25)')
    eth_row.background_color('Chg', 'rgba(244,67,54,0.25)')
    sol_row.background_color('Chg', 'rgba(76,175,80,0.25)')

    # ── Boot ──────────────────────────────────────────────────────────────────
    # show(block=False) starts webview + waits for page load.
    # run_script_and_get calls are safe after this returns.
    chart.show(block=False)

    # ==========================================================================
    # Chart API
    # ==========================================================================
    print("\n=== Chart API ===")
    opts = chart.options()
    print(f"layout.background:  {opts.get('layout', {}).get('background', {})}")
    print(f"auto_size_active:   {chart.auto_size_active()}")
    print(f"get_pane_count:     {chart.get_pane_count()}")
    panes = chart.panes()
    print(f"panes() count:      {len(panes)}")
    print(f"pane_size(0):       {chart.pane_size(0)}")

    # swap panes 2↔3 then revert
    chart.swap_panes(2, 3)
    print(f"after swap_panes(2,3) pane count: {chart.get_pane_count()}")
    chart.swap_panes(2, 3)
    print("swap reverted")

    # crosshair: set then clear using first kama10 point
    first = kama10.data_by_index(0)
    if first:
        chart.set_crosshair_position(first['value'], first['time'], kama10)
        print(f"set_crosshair_position → t={first['time']}, v={first['value']:.4f}")
        chart.clear_crosshair_position()
        print("clear_crosshair_position → ok")

    # ==========================================================================
    # Pane API
    # ==========================================================================
    print("\n=== Pane API ===")
    panes = chart.panes()
    panes[0].set_stretch_factor(3.0)
    panes[1].set_stretch_factor(1.5)
    panes[2].set_stretch_factor(1.0)

    for i, p in enumerate(panes):
        sf    = p.get_stretch_factor()
        h     = p.get_height()
        names = [s.name for s in p.get_series()]
        print(f"  pane[{i}]: idx={p.pane_index()}, stretch={sf:.1f}, h={h}px, series={names}")

    # ==========================================================================
    # Series API
    # ==========================================================================
    print("\n=== Series API ===")
    print(f"kama10.series_type:     {kama10.series_type()}")
    print(f"kama10.series_order:    {kama10.series_order()}")
    print(f"kama10.get_pane index:  {kama10.get_pane().pane_index()}")
    print(f"adx.get_pane index:     {adx.get_pane().pane_index()}")
    print(f"rsi.get_pane index:     {rsi.get_pane().pane_index()}")
    print(f"bbp.get_pane index:     {bbp.get_pane().pane_index()}")

    data = kama10.get_data()
    print(f"kama10 get_data len:    {len(data)}")
    print(f"kama10 data_by_index(0):          {kama10.data_by_index(0)}")
    print(f"kama10 data_by_index(0, nearest_right): {kama10.data_by_index(0, 'nearest_right')}")
    print(f"kama10 last_value_data: {kama10.last_value_data()}")
    print(f"kama10 bars_in_logical_range(0,10): {kama10.bars_in_logical_range(0, 10)}")

    if data:
        coord = kama10.price_to_coordinate(data[0]['value'])
        print(f"price_to_coordinate({data[0]['value']:.2f}): {coord}")
        if coord:
            back = kama10.coordinate_to_price(coord)
            print(f"coordinate_to_price({coord:.2f}): {back:.4f}")

    print(f"adx.options color:      {adx.options().get('color', 'n/a')}")
    print(f"adx.get_data len:       {len(adx.get_data())}")
    print(f"adx.series_order:       {adx.series_order()}")

    kama10.set_series_order(10)
    print(f"kama10 series_order after set(10): {kama10.series_order()}")

    # move_to_pane: kama10 → pane 1 → back to pane 0
    kama10.move_to_pane(1)
    print(f"kama10 after move_to_pane(1): pane={kama10.get_pane().pane_index()}")
    sleep(10)
    kama10.move_to_pane(0)
    print(f"kama10 after move_to_pane(0): pane={kama10.get_pane().pane_index()}")
    
    print("Removing (hiding) ADX series...")
    
    print("\n[Ready — interact with chart; click table rows to test callback]")
    chart.show(block=True)
