from typing import Optional
import pandas as pd

from ..util import Pane, js_data


class VolumeProfile(Pane):
    """
    Displays a volume profile (price-level histogram) overlaid on the chart.
    Uses Lib.Plugins.VolumeProfile from plugins.js.

    The plugin is attached to the main candlestick series. Volume bars are drawn
    on the right side of the chart with configurable width.

    :param chart: The parent chart instance.
    :param up_color: Color for bars where close >= open.
    :param down_color: Color for bars where close < open.
    :param width_factor: Fraction (0–1) of chart width used for the profile (default 0.4).
    """

    def __init__(
        self,
        chart,
        up_color: str = 'rgba(38,166,154,0.5)',
        down_color: str = 'rgba(239,83,80,0.5)',
        width_factor: float = 0.4,
    ):
        super().__init__(chart.win)
        self._chart = chart
        self.run_script(f'''
            {self.id} = new Lib.Plugins.VolumeProfile({{
                upColor: '{up_color}',
                downColor: '{down_color}',
                widthFactor: {width_factor},
            }});
            {chart.id}.series.attachPrimitive({self.id});
        null''')

    def set_data(self, df: pd.DataFrame):
        """
        Feeds OHLCV data to the volume profile.

        :param df: DataFrame with columns: time, open, high, low, close, volume.
        """
        self.run_script(f'{self.id}.setData({js_data(df)})')

    def apply_options(
        self,
        up_color: Optional[str] = None,
        down_color: Optional[str] = None,
        width_factor: Optional[float] = None,
    ):
        """Updates volume profile display options."""
        opts = {}
        if up_color is not None:
            opts['upColor'] = up_color
        if down_color is not None:
            opts['downColor'] = down_color
        if width_factor is not None:
            opts['widthFactor'] = width_factor
        if opts:
            import json
            self.run_script(f'{self.id}.applyOptions({json.dumps(opts)})')
