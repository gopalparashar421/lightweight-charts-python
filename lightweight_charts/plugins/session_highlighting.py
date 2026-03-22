import json
from typing import Optional, List

from ..util import Pane, js_data, js_json


class SessionHighlighting(Pane):
    """
    Highlights chart background for specific time ranges (e.g. market sessions).
    Uses Lib.Plugins.SessionHighlighting from plugins.js.

    :param chart: The parent chart instance.
    :param session_color: Default RGBA color for session highlight bands.
    """

    def __init__(self, chart, session_color: str = 'rgba(41, 98, 255, 0.08)'):
        super().__init__(chart.win)
        self._chart = chart
        self.run_script(f'''
            {self.id} = new Lib.Plugins.SessionHighlighting({{
                sessionColor: '{session_color}',
            }});
            {chart.id}.series.attachPrimitive({self.id});
        null''')

    def set_data(self, sessions: List[dict]):
        """
        Sets the session ranges to highlight.

        :param sessions: A list of dicts with keys ``start`` and ``end``
            (Unix timestamps in seconds), and an optional ``color`` key.
            Example::

                [
                    {'start': 1700000000, 'end': 1700003600},
                    {'start': 1700007200, 'end': 1700010800, 'color': 'rgba(255,0,0,0.1)'},
                ]
        """
        self.run_script(f'{self.id}.setData({json.dumps(sessions)})')

    def apply_options(self, session_color: Optional[str] = None):
        """Updates the default session color."""
        opts = {}
        if session_color is not None:
            opts['sessionColor'] = session_color
        if opts:
            self.run_script(f'{self.id}.applyOptions({json.dumps(opts)})')
