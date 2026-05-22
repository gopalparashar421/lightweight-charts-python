from .abstract import AbstractChart, Window, Line, Area, Histogram, AttachedPrimitive, UpDownMarkers, Pane, SeriesCommon
from .chart import Chart
from .widgets import JupyterChart
from .polygon import PolygonChart
from .plugins import (
    SessionHighlighting,
    Tooltip,
    BandsIndicator,
    VolumeProfile,
    HeatmapSeries,
    PositionTool,
)

try:
    from .stream import StreamChart
except ImportError:
    class StreamChart:  # type: ignore[no-redef]
        """Placeholder: install lightweight-charts[stream] to use StreamChart."""

        def __new__(cls, *args, **kwargs):
            raise ImportError(
                "StreamChart requires optional dependencies. "
                "Install them with: pip install lightweight-charts[stream]"
            )

__all__ = [
    'AbstractChart',
    'Window',
    'Line',
    'Area',
    'Histogram',
    'AttachedPrimitive',
    'UpDownMarkers',
    'Chart',
    'JupyterChart',
    'PolygonChart',
    'SeriesCommon',
    'SessionHighlighting',
    'Tooltip',
    'BandsIndicator',
    'VolumeProfile',
    'HeatmapSeries',
    'PositionTool',
    'Pane',
    'StreamChart',
]