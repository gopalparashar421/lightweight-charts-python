from typing import TYPE_CHECKING

from ..util import Pane

if TYPE_CHECKING:
    from ..abstract import SeriesCommon


class BandsIndicator(Pane):
    """
    Draws band lines and a fill region between an upper and lower series.

    Typical uses include Bollinger Bands, Donchian Channels, or any custom
    upper/lower envelope.  The upper and lower series must be ``Line`` series
    whose ``value`` column provides the band levels at each timestamp.

    :param upper_series: Line series whose values define the upper band.
    :param lower_series: Line series whose values define the lower band.
    :param line_color: Color of the upper and lower band lines.
    :param fill_color: Fill color of the region between the bands.
    :param line_width: Width of the band lines in pixels.
    """

    def __init__(
        self,
        upper_series: "SeriesCommon",
        lower_series: "SeriesCommon",
        line_color: str = 'rgb(25, 200, 100)',
        fill_color: str = 'rgba(25, 200, 100, 0.25)',
        line_width: int = 1,
    ):
        super().__init__(upper_series._chart.win)
        self._upper_series = upper_series
        self._lower_series = lower_series
        self.run_script(f'''
            {self.id} = new Lib.BandsIndicator(
                {upper_series.id}.series,
                {lower_series.id}.series,
                {{
                    lineColor: '{line_color}',
                    fillColor: '{fill_color}',
                    lineWidth: {line_width},
                }}
            );
            {upper_series.id}.series.attachPrimitive({self.id});
        null''')

    def delete(self):
        """Detaches and removes the bands indicator from the series."""
        self.run_script(f'{self._upper_series.id}.series.detachPrimitive({self.id})')
