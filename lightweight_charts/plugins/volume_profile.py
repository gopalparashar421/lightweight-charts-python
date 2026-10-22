import json

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
        ``{'price': float, 'vol': float, 'color': str}`` dicts or a DataFrame with
        ``price``, ``vol``, and optional ``color`` columns.
    :param width: Width of the profile in bar units (default 10).
    """

    def __init__(
        self,
        series,
        time,
        profile: list[dict] | pd.DataFrame,
        width: int = 10,
    ):
        super().__init__(series._chart.win)
        self._series = series
        ts = series._chart._format_time(time)
        profile_list = self._profile_records(profile)
        self._vpData_time = ts
        self._vpData_width = width
        vp_data = {"time": ts, "profile": profile_list, "width": width}
        self.run_script(f"""
            {self.id} = new Lib.VolumeProfile(
                {series._chart.id}.chart,
                {series.id}.series,
                {json.dumps(vp_data)}
            );
            {series.id}.series.attachPrimitive({self.id});
        null""")

    @staticmethod
    def _profile_records(profile: list[dict] | pd.DataFrame) -> list[dict]:
        if isinstance(profile, pd.DataFrame):
            cols = [c for c in ("price", "vol", "color") if c in profile.columns]
            return profile[cols].to_dict("records")
        return profile

    def update_data(
        self,
        profile: list[dict] | pd.DataFrame,
        time=None,
        width: int | None = None,
    ) -> None:
        """Replace profile data in-place without detaching the primitive."""
        ts = self._series._chart._format_time(time) if time is not None else self._vpData_time
        if time is not None:
            self._vpData_time = ts
        if width is not None:
            self._vpData_width = width
        profile_list = self._profile_records(profile)
        w = width if width is not None else self._vpData_width
        vp_data = {"time": ts, "profile": profile_list, "width": w}
        self.run_script(f"{self.id}.updateData({json.dumps(vp_data)})")

    def delete(self):
        """Detaches and removes the volume profile from the series."""
        self.run_script(f"{self._series.id}.series.detachPrimitive({self.id})")
