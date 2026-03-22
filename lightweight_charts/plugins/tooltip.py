from typing import Optional

from ..util import Pane


class Tooltip(Pane):
    """
    Floating tooltip that shows OHLCV or value data near the crosshair.
    Uses Lib.Plugins.Tooltip from plugins.js.

    :param chart: The parent chart instance.
    :param title: Optional title shown at the top of the tooltip.
    :param font_size: Font size in pixels (default 12).
    :param color: Text color (default near-white).
    :param background: Background color (default semi-transparent black).
    """

    def __init__(
        self,
        chart,
        title: str = '',
        font_size: int = 12,
        color: str = 'rgba(255,255,255,0.9)',
        background: str = 'rgba(15,15,15,0.8)',
    ):
        super().__init__(chart.win)
        self._chart = chart
        self.run_script(f'''
            {self.id} = new Lib.Plugins.Tooltip({{
                title: '{title}',
                fontSize: {font_size},
                color: '{color}',
                background: '{background}',
            }});
            {chart.id}.series.attachPrimitive({self.id});
        null''')

    def apply_options(
        self,
        title: Optional[str] = None,
        font_size: Optional[int] = None,
        color: Optional[str] = None,
        background: Optional[str] = None,
    ):
        """Updates tooltip display options."""
        opts = {}
        if title is not None:
            opts['title'] = title
        if font_size is not None:
            opts['fontSize'] = font_size
        if color is not None:
            opts['color'] = color
        if background is not None:
            opts['background'] = background
        if opts:
            import json
            self.run_script(f'{self.id}.applyOptions({json.dumps(opts)})')
