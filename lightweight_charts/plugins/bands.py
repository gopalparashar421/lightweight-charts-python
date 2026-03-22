from typing import Optional, TYPE_CHECKING
import json

from ..util import Pane

if TYPE_CHECKING:
    from ..abstract import SeriesCommon


class BandsIndicator(Pane):
    """
    Draws a filled band between an upper and lower line/area series.
    Uses Lib.Plugins.BandsIndicator from plugins.js.

    The plugin is attached to the upper series, but reads data from both
    upper and lower series to compute the fill region.

    :param chart: The parent chart instance.
    :param upper_series: The upper boundary series (Line or Area).
    :param lower_series: The lower boundary series (Line or Area).
    :param fill_color: Fill color for the band.
    :param upper_color: Line color for the upper boundary (unused by current renderer).
    :param lower_color: Line color for the lower boundary (unused by current renderer).
    :param line_width: Line width (unused by current renderer).
    """

    def __init__(
        self,
        chart,
        upper_series: "SeriesCommon",
        lower_series: "SeriesCommon",
        fill_color: str = 'rgba(33,150,243,0.1)',
        upper_color: str = '#2196F3',
        lower_color: str = '#2196F3',
        line_width: int = 1,
    ):
        super().__init__(chart.win)
        self._chart = chart
        self.run_script(f'''
            {self.id} = new Lib.Plugins.BandsIndicator(
                {upper_series.id}.series,
                {lower_series.id}.series,
                {{
                    fillColor: '{fill_color}',
                    upperColor: '{upper_color}',
                    lowerColor: '{lower_color}',
                    lineWidth: {line_width},
                }}
            );
            {upper_series.id}.series.attachPrimitive({self.id});
        null''')

    def apply_options(
        self,
        fill_color: Optional[str] = None,
        upper_color: Optional[str] = None,
        lower_color: Optional[str] = None,
        line_width: Optional[int] = None,
    ):
        """Updates band display options."""
        opts = {}
        if fill_color is not None:
            opts['fillColor'] = fill_color
        if upper_color is not None:
            opts['upperColor'] = upper_color
        if lower_color is not None:
            opts['lowerColor'] = lower_color
        if line_width is not None:
            opts['lineWidth'] = line_width
        if opts:
            self.run_script(f'{self.id}.applyOptions({json.dumps(opts)})')
