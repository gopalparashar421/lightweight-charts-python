from typing import Optional, List
import json
import pandas as pd

from ..abstract import SeriesCommon
from ..util import Pane, js_data


class HeatmapSeries(SeriesCommon):
    """
    A custom series that renders a price-level heatmap (e.g. orderbook liquidity).
    Uses Lib.Plugins.HeatmapSeries (a custom series pane view) from plugins.js.

    Each data point must have: ``time`` (Unix ts), ``low`` (float), ``high`` (float),
    and ``value`` (float, 0–1 intensity).

    :param chart: The parent chart instance.
    :param color_scale: Optional list of ``[r, g, b, a]`` stops or CSS color strings
        that define the color gradient from 0 (min intensity) to 1 (max intensity).
    :param pane_index: Pane to render in (default 0).
    """

    def __init__(
        self,
        chart,
        color_scale: Optional[List] = None,
        pane_index: int = None,
    ):
        super().__init__(chart, '', pane_index)
        color_scale_js = json.dumps(color_scale) if color_scale else 'null'
        self.run_script(f'''
            {self.id} = {chart.id}.createCustomSeries(
                new Lib.Plugins.HeatmapSeries({{
                    colorScale: {color_scale_js},
                }}),
                {{}},
                {pane_index if pane_index is not None else 0}
            )
        null''')

    def set(self, df: pd.DataFrame, format_cols: bool = True):
        """
        Sets the heatmap data.

        :param df: DataFrame with columns: time, low, high, value.
        :param format_cols: Whether to run datetime formatting on the time column.
        """
        if df is None or df.empty:
            self.run_script(f'{self.id}.series.setData([])')
            return
        if format_cols:
            df = self._df_datetime_format(df)
        self.run_script(f'{self.id}.series.setData({js_data(df)})')

    def update(self, series: pd.Series):
        """Updates or appends a single heatmap bar."""
        series = self._series_datetime_format(series)
        self.run_script(f'{self.id}.series.update({js_data(series)})')
