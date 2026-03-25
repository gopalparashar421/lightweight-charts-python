import json
from typing import Optional

from ..util import Pane


class Tooltip(Pane):
    """
    Floating tooltip that follows the crosshair and shows price and date/time.

    Uses the ``TooltipPrimitive`` from lightweight-charts and attaches to a series.
    The chart's crosshair is automatically switched to Magnet mode.

    :param series: The series to attach to.
    :param line_color: Color of the vertical crosshair guide line.
    :param follow_mode: ``'top'`` (pinned to the top of the pane) or
        ``'tracking'`` (follows the cursor vertically).
    :param title: Optional title shown at the top of the tooltip box.
    """

    def __init__(
        self,
        series,
        line_color: str = 'rgba(0, 0, 0, 0.2)',
        follow_mode: str = 'top',
        title: str = '',
    ):
        super().__init__(series._chart.win)
        self._series = series
        opts = {
            'lineColor': line_color,
            'tooltip': {
                'followMode': follow_mode,
                'title': title,
            },
        }
        self.run_script(f'''
            {self.id} = new Lib.TooltipPrimitive({json.dumps(opts)});
            {series.id}.series.attachPrimitive({self.id});
        null''')

    def apply_options(
        self,
        line_color: Optional[str] = None,
        follow_mode: Optional[str] = None,
        title: Optional[str] = None,
    ):
        """Updates tooltip display options."""
        opts = {}
        tooltip_opts = {}
        if line_color is not None:
            opts['lineColor'] = line_color
        if follow_mode is not None:
            tooltip_opts['followMode'] = follow_mode
        if title is not None:
            tooltip_opts['title'] = title
        if tooltip_opts:
            opts['tooltip'] = tooltip_opts
        if opts:
            self.run_script(f'{self.id}.applyOptions({json.dumps(opts)})')

    def delete(self):
        """Detaches and removes the tooltip from the series."""
        self.run_script(f'{self._series.id}.series.detachPrimitive({self.id})')
