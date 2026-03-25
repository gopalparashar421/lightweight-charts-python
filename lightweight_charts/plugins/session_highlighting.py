import json
from typing import List

from ..util import Pane


class SessionHighlighting(Pane):
    """
    Highlights chart background for specific time ranges (e.g. trading sessions).

    Each bar's timestamp is checked against the supplied session windows; the first
    matching window's color is applied.  Bars outside all windows use
    ``default_color``.

    :param series: The series to attach to.
    :param default_color: Background color for bars that fall outside all sessions.
        Use ``'rgba(0,0,0,0)'`` for transparent (no highlight).
    """

    def __init__(self, series, default_color: str = 'rgba(0,0,0,0)'):
        super().__init__(series._chart.win)
        self._series = series
        sessions_var = self.id + 'S'
        self._sessions_var = sessions_var
        self.run_script(f'''
            {sessions_var} = [];
            {self.id} = new Lib.SessionHighlighting(function(time) {{
                var ts = typeof time === 'number' ? time * 1000 : new Date(time).getTime();
                for (var i = 0; i < {sessions_var}.length; i++) {{
                    var s = {sessions_var}[i];
                    if (ts >= s.start && ts <= s.end) return s.color;
                }}
                return '{default_color}';
            }});
            {series.id}.series.attachPrimitive({self.id});
        null''')

    def set_sessions(self, sessions: List[dict]):
        """
        Sets the time ranges to highlight.

        :param sessions: List of dicts with ``start`` and ``end`` as Unix timestamps
            (seconds) and an optional ``color`` (CSS color string).  Example::

                [
                    {'start': 1704099600, 'end': 1704110400},
                    {'start': 1704103200, 'end': 1704106800, 'color': 'rgba(255,0,0,0.1)'},
                ]
        """
        js_sessions = json.dumps([
            {
                'start': s['start'] * 1000,
                'end':   s['end']   * 1000,
                'color': s.get('color', 'rgba(41, 98, 255, 0.08)'),
            }
            for s in sessions
        ])
        self.run_script(f'''
            {self._sessions_var} = {js_sessions};
            {self.id}.dataUpdated('full');
        null''')

    def delete(self):
        """Detaches and removes the session highlighting from the series."""
        self.run_script(f'{self._series.id}.series.detachPrimitive({self.id})')
