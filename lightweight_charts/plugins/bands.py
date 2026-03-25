from typing import Optional, TYPE_CHECKING

from ..util import Pane

if TYPE_CHECKING:
    from ..abstract import SeriesCommon


class BandsIndicator(Pane):
    """
    Draws ±10% band lines around a single series as an attached primitive.

    Upper and lower bands are auto-calculated from the series data
    (``upper = value × 1.1``, ``lower = value × 0.9``).

    :param series: The series to attach to.
    :param line_color: Color of the upper and lower band lines.
    :param fill_color: Fill color of the region between the bands.
    :param line_width: Width of the band lines in pixels.
    """

    def __init__(
        self,
        series: "SeriesCommon",
        line_color: str = 'rgb(25, 200, 100)',
        fill_color: str = 'rgba(25, 200, 100, 0.25)',
        line_width: int = 1,
    ):
        super().__init__(series._chart.win)
        self._series = series
        self.run_script(f'''
            {self.id} = new Lib.BandsIndicator({{
                lineColor: '{line_color}',
                fillColor: '{fill_color}',
                lineWidth: {line_width},
            }});
            {series.id}.series.attachPrimitive({self.id});
        null''')

    def delete(self):
        """Detaches and removes the bands indicator from the series."""
        self.run_script(f'{self._series.id}.series.detachPrimitive({self.id})')
