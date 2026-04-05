import json
from typing import Optional, List
import pandas as pd

from ..util import Pane


class HeatmapSeries(Pane):
    """
    Custom series that renders a price-level heatmap (e.g. order-book liquidity).

    Uses ``HeatMapSeries`` (an ``ICustomSeriesPaneView``) which is added directly
    to the chart via ``chart.addCustomSeries``.

    The public API accepts raw orderbook snapshots via :meth:`set` and
    :meth:`update`.  Each ``(price, size)`` tuple becomes one heatmap cell
    coloured according to *bid_color* or *ask_color*.

    An internal :meth:`_set` / :meth:`_update` API accepts pre-built cell data
    (``time``, ``low``, ``high``, ``amount`` columns) for custom data pipelines.

    :param chart: The parent chart instance.
    :param cell_shader_js: Optional JavaScript function string
        ``(amount: number) => string`` that maps an amount to a CSS color.
        Only used for cells that do not carry an explicit ``color`` field and
        have no matching side shader.
        Defaults to a green gradient where 0 → dim, 100 → bright.
    :param cell_border_width: Cell border width in pixels.
    :param cell_border_color: CSS color for cell borders.
    :param bid_color: Flat CSS color applied to bid-side cells when no
        *bid_shader_js* is provided.
    :param ask_color: Flat CSS color applied to ask-side cells when no
        *ask_shader_js* is provided.
    :param bid_shader_js: Optional JavaScript function string
        ``(amount: number) => string`` for bid cells.  Overrides *bid_color*.
    :param ask_shader_js: Optional JavaScript function string
        ``(amount: number) => string`` for ask cells.  Overrides *ask_color*.
    :param pane_index: Pane to render in (default 0).
    """

    def __init__(
        self,
        chart,
        cell_shader_js: Optional[str] = None,
        cell_border_width: int = 1,
        cell_border_color: str = 'transparent',
        bid_color: str = 'rgba(0, 160, 80, 0.6)',
        ask_color: str = 'rgba(200, 50, 50, 0.6)',
        bid_shader_js: Optional[str] = None,
        ask_shader_js: Optional[str] = None,
        pane_index: int = 0,
    ):
        super().__init__(chart.win)
        self._chart = chart
        self._bid_color = bid_color
        self._ask_color = ask_color
        self._bid_shader_js = bid_shader_js
        self._ask_shader_js = ask_shader_js
        view_var = self.id + 'V'
        base_opts = json.dumps({
            'cellBorderWidth': cell_border_width,
            'cellBorderColor': cell_border_color,
        })
        # Strip the trailing '}' so we can append optional function fields
        opts_str = base_opts[:-1]
        if cell_shader_js:
            opts_str += f', "cellShader": {cell_shader_js}'
        if bid_shader_js:
            opts_str += f', "bidShader": {bid_shader_js}'
        if ask_shader_js:
            opts_str += f', "askShader": {ask_shader_js}'
        opts_str += '}'
        self.run_script(f'''
            {view_var} = new Lib.HeatMapSeries();
            {self.id} = {chart.id}.chart.addCustomSeries({view_var}, {opts_str}, {pane_index});
        null''')

    def _set(self, df: pd.DataFrame):
        """
        Sets the heatmap data.

        :param df: DataFrame with columns ``time``, ``low``, ``high``, and
            ``value`` (or ``amount``).  One row per price cell; rows sharing
            the same ``time`` are grouped into one bar.
        """
        if df is None or df.empty:
            self.run_script(f'{self.id}.setData([])')
            return
        df = df.copy()
        if 'value' in df.columns and 'amount' not in df.columns:
            df = df.rename(columns={'value': 'amount'})
        if not pd.api.types.is_datetime64_any_dtype(df['time']):
            df['time'] = pd.to_datetime(df['time'])
        df['time'] = df['time'].astype('int64') // 10 ** 9
        records = []
        for t, group in df.groupby('time', sort=True):
            cells = group[['low', 'high', 'amount']].to_dict('records')
            records.append({'time': int(t), 'cells': cells})
        self.run_script(f'{self.id}.setData({json.dumps(records)})')

    def set(
        self,
        time,
        bids: List[tuple],
        asks: List[tuple],
    ):
        """
        Replace all heatmap data with a single orderbook snapshot at *time*.

        :param time: The bar's timestamp (Unix seconds, datetime, or string).
        :param bids: List of ``(price, size)`` tuples for the bid side.
        :param asks: List of ``(price, size)`` tuples for the ask side.
        """
        cells = []
        for price, size in bids:
            p = float(price)
            cell: dict = {'low': p, 'high': p + 1.0, 'amount': float(size), 'side': 'bid'}
            if not self._bid_shader_js:
                cell['color'] = self._bid_color
            cells.append(cell)
        for price, size in asks:
            p = float(price)
            cell = {'low': p, 'high': p + 1.0, 'amount': float(size), 'side': 'ask'}
            if not self._ask_shader_js:
                cell['color'] = self._ask_color
            cells.append(cell)
        ts = int(pd.Timestamp(time).timestamp())
        self.run_script(f'{self.id}.setData({json.dumps([{"time": ts, "cells": cells}])})')

    def update(
        self,
        time,
        bids: List[tuple],
        asks: List[tuple],
    ):
        """
        Append or update the heatmap bar at *time* with a new orderbook snapshot.

        :param time: The bar's timestamp (Unix seconds, datetime, or string).
        :param bids: List of ``(price, size)`` tuples for the bid side.
        :param asks: List of ``(price, size)`` tuples for the ask side.
        """
        cells = []
        for price, size in bids:
            p = float(price)
            cell: dict = {'low': p, 'high': p + 1.0, 'amount': float(size), 'side': 'bid'}
            if not self._bid_shader_js:
                cell['color'] = self._bid_color
            cells.append(cell)
        for price, size in asks:
            p = float(price)
            cell = {'low': p, 'high': p + 1.0, 'amount': float(size), 'side': 'ask'}
            if not self._ask_shader_js:
                cell['color'] = self._ask_color
            cells.append(cell)
        self._update(time, cells)

    def _update(self, time, cells: List[dict]):
        """
        Appends or updates a single bar.

        :param time: The bar's timestamp (Unix seconds, datetime, or string).
        :param cells: List of ``{'low': float, 'high': float, 'amount': float}`` dicts.
        """
        ts = int(pd.Timestamp(time).timestamp())
        self.run_script(f'{self.id}.update({json.dumps({"time": ts, "cells": cells})})')
