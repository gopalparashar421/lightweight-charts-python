import json
from typing import Optional, List
import pandas as pd

from ..util import Pane


class HeatmapSeries(Pane):
    """
    Custom series that renders a price-level heatmap (e.g. order-book liquidity).

    Uses ``HeatMapSeries`` (an ``ICustomSeriesPaneView``) which is added directly
    to the chart via ``chart.addCustomSeries``.

    Each data bar holds multiple price cells.  Supply a DataFrame where each row
    is one cell, with columns ``time``, ``low``, ``high``, and ``value`` (or
    ``amount``).  Rows that share the same ``time`` are grouped into one bar.

    :param chart: The parent chart instance.
    :param cell_shader_js: Optional JavaScript function string
        ``(amount: number) => string`` that maps an amount to a CSS color.
        Defaults to a green gradient where 0 → dim, 100 → bright.
    :param cell_border_width: Cell border width in pixels.
    :param cell_border_color: CSS color for cell borders.
    :param pane_index: Pane to render in (default 0).
    """

    def __init__(
        self,
        chart,
        cell_shader_js: Optional[str] = None,
        cell_border_width: int = 1,
        cell_border_color: str = 'transparent',
        pane_index: int = 0,
    ):
        super().__init__(chart.win)
        self._chart = chart
        view_var = self.id + 'V'
        base_opts = json.dumps({
            'cellBorderWidth': cell_border_width,
            'cellBorderColor': cell_border_color,
        })
        if cell_shader_js:
            opts_str = base_opts[:-1] + f', "cellShader": {cell_shader_js}}}'
        else:
            opts_str = base_opts
        self.run_script(f'''
            {view_var} = new Lib.HeatMapSeries();
            {self.id} = {chart.id}.chart.addCustomSeries({view_var}, {opts_str}, {pane_index});
        null''')

    def set(self, df: pd.DataFrame):
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

    def update(self, time, cells: List[dict]):
        """
        Appends or updates a single bar.

        :param time: The bar's timestamp (Unix seconds, datetime, or string).
        :param cells: List of ``{'low': float, 'high': float, 'amount': float}`` dicts.
        """
        ts = int(pd.Timestamp(time).timestamp())
        self.run_script(f'{self.id}.update({json.dumps({"time": ts, "cells": cells})})')
