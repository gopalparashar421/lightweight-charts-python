import json
from typing import Union, List
import pandas as pd

from ..util import Pane


class VolumeProfile(Pane):
    """
    Renders a volume-profile histogram at a specific time position on a series.

    The profile is a vertical bar chart of price levels vs. volume, anchored at
    ``time`` and spanning ``width`` bars to the right.

    :param series: The series to attach to (also provides the chart reference).
    :param time: Anchor timestamp for the profile (Unix seconds, datetime, or string).
    :param profile: Price-level volume data — either a list of
        ``{'price': float, 'vol': float}`` dicts or a DataFrame with
        ``price`` and ``vol`` columns.
    :param width: Width of the profile in bar units (default 10).
    """

    def __init__(
        self,
        series,
        time,
        profile: Union[List[dict], pd.DataFrame],
        width: int = 10,
    ):
        super().__init__(series._chart.win)
        self._series = series
        ts = series._chart._single_datetime_format(time)
        profile_list = (
            profile[['price', 'vol']].to_dict('records')
            if isinstance(profile, pd.DataFrame)
            else profile
        )
        vp_data = {'time': ts, 'profile': profile_list, 'width': width}
        self.run_script(f'''
            {self.id} = new Lib.VolumeProfile(
                {series._chart.id}.chart,
                {series.id}.series,
                {json.dumps(vp_data)}
            );
            {series.id}.series.attachPrimitive({self.id});
        null''')

    def delete(self):
        """Detaches and removes the volume profile from the series."""
        self.run_script(f'{self._series.id}.series.detachPrimitive({self.id})')
