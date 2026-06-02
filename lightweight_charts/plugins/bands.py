from typing import TYPE_CHECKING

import pandas as pd

from ..abstract import Line
from ..util import Pane

if TYPE_CHECKING:
    from ..abstract import AbstractChart


class BandsIndicator(Pane):
    """
    Draws band lines and a fill region between an upper and lower series.

    Typical uses include Bollinger Bands, Donchian Channels, or any custom
    upper/lower envelope.

    :param chart: The chart instance to attach the bands to.
    :param upper_data: DataFrame with ``time`` and ``value`` columns for the upper band.
    :param lower_data: DataFrame with ``time`` and ``value`` columns for the lower band.
    :param line_color: Color of the upper and lower band lines (default: transparent).
    :param fill_color: Fill color of the region between the bands.
    :param line_width: Width of the band lines in pixels (default: 0).
    """

    def __init__(
        self,
        chart: "AbstractChart",
        upper_data: pd.DataFrame,
        lower_data: pd.DataFrame,
        line_color: str = "rgba(0,0,0,0)",
        fill_color: str = "rgba(25, 200, 100, 0.25)",
        line_width: int = 0,
    ):
        super().__init__(chart.win)

        # Hidden internal series — always invisible, no labels, no crosshair markers.
        self._upper_line = Line(
            chart,
            "",
            "rgba(0,0,0,0)",
            "solid",
            "simple",
            0,
            False,
            False,
            crosshair_marker=False,
        )
        chart._lines.append(self._upper_line)
        self._upper_line.set(upper_data)

        self._lower_line = Line(
            chart,
            "",
            "rgba(0,0,0,0)",
            "solid",
            "simple",
            0,
            False,
            False,
            crosshair_marker=False,
        )
        chart._lines.append(self._lower_line)
        self._lower_line.set(lower_data)

        self.run_script(f"""
            {self.id} = new Lib.BandsIndicator(
                {self._upper_line.id}.series,
                {self._lower_line.id}.series,
                {{
                    lineColor: '{line_color}',
                    fillColor: '{fill_color}',
                    lineWidth: {line_width},
                }}
            );
            {self._upper_line.id}.series.attachPrimitive({self.id});
        null""")

    def delete(self):
        """Detaches and removes the bands indicator and its internal series."""
        self.run_script(f"{self._upper_line.id}.series.detachPrimitive({self.id})")
        self._upper_line.delete()
        self._lower_line.delete()
