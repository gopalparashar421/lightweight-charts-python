import json
import inspect
import asyncio
import os
from base64 import b64decode
from datetime import datetime
from typing import Callable, Union, Literal, List, Optional
import pandas as pd

from .table import Table
from .toolbox import ToolBox
from .drawings import (
    Box,
    HorizontalLine,
    RayLine,
    TrendLine,
    TwoPointDrawing,
    VerticalLine,
    VerticalSpan,
)
from .topbar import TopBar
from .util import (
    BulkRunScript,
    Pane as _PaneBase,
    Events,
    IDGen,
    as_enum,
    jbool,
    js_json,
    TIME,
    NUM,
    FLOAT,
    LINE_STYLE,
    LINE_TYPE,
    LAST_PRICE_ANIMATION_MODE,
    MARKER_POSITION,
    MARKER_SHAPE,
    CROSSHAIR_MODE,
    PRICE_SCALE_MODE,
    marker_position,
    marker_shape,
    js_data,
)

current_dir = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(current_dir, "js", "index.html")


class Window:
    _id_gen = IDGen()
    handlers = {}

    def __init__(
        self,
        script_func: Optional[Callable] = None,
        js_api_code: Optional[str] = None,
        run_script: Optional[Callable] = None,
    ):
        self.loaded = False
        self.script_func = script_func
        self.scripts = []
        self.final_scripts = []
        self.bulk_run = BulkRunScript(script_func)

        if run_script:
            self.run_script = run_script

        if js_api_code:
            self.run_script(f"window.callbackFunction = {js_api_code}")

    def on_js_load(self):
        if self.loaded:
            return
        self.loaded = True

        if hasattr(self, "_return_q"):
            while not self.run_script_and_get('document.readyState == "complete"'):
                continue  # scary, but works

        initial_script = ""
        self.scripts.extend(self.final_scripts)
        for script in self.scripts:
            initial_script += f"\n{script}"
        self.script_func(initial_script)

    def run_script(self, script: str, run_last: bool = False):
        """
        For advanced users; evaluates JavaScript within the Webview.
        """

        if self.script_func is None:
            raise AttributeError("script_func has not been set")
        if self.loaded:
            if self.bulk_run.enabled:
                self.bulk_run.add_script(script)
            else:
                self.script_func(script)
        elif run_last:
            self.final_scripts.append(script)
        else:
            self.scripts.append(script)

    def run_script_and_get(self, script: str):
        self.run_script(f"_~_~RETURN~_~_{script}")
        return self._return_q.get()

    def create_table(
        self,
        width: NUM,
        height: NUM,
        headings: tuple,
        widths: Optional[tuple] = None,
        alignments: Optional[tuple] = None,
        position: FLOAT = "left",
        draggable: bool = False,
        background_color: str = "#121417",
        border_color: str = "rgb(70, 70, 70)",
        border_width: int = 1,
        heading_text_colors: Optional[tuple] = None,
        heading_background_colors: Optional[tuple] = None,
        return_clicked_cells: bool = False,
        func: Optional[Callable] = None,
    ) -> "Table":
        return Table(*locals().values())

    def style(
        self,
        background_color: str = "#0c0d0f",
        hover_background_color: str = "#3c434c",
        click_background_color: str = "#50565E",
        active_background_color: str = "rgba(0, 122, 255, 0.7)",
        muted_background_color: str = "rgba(0, 122, 255, 0.3)",
        border_color: str = "#3C434C",
        color: str = "#d8d9db",
        active_color: str = "#ececed",
    ):
        self.run_script(f"Lib.Handler.setRootStyles({js_json(locals())});")


class SeriesCommon(_PaneBase):
    def __init__(self, chart: "AbstractChart", name: str = "", pane_index: int = None):
        super().__init__(chart.win)
        self._chart = chart
        if hasattr(chart, "_interval"):
            self._interval = chart._interval
        else:
            self._interval = 1
        self._last_bar = None
        self.name = name
        self.num_decimals = 2
        self.offset = 0
        self.data = pd.DataFrame()
        self.markers = {}
        self.pane_index = pane_index
        self._data_changed_handler_id: Optional[str] = None
        if hasattr(chart, '_series_registry'):
            chart._series_registry.append(self)

    def legend(
        self,
        visible: bool = True,
        lines: bool = True,
        color: str = "rgb(191, 195, 203)",
        font_size: int = 11,
        font_family: str = "Monaco",
        text: str = "",
    ):
        """
        Configures the legend for the pane this series lives on.
        OHLC and percent are intentionally omitted — use chart.legend() on pane 0 for those.
        """
        pane_idx = self.pane_index if self.pane_index is not None else 0
        self._chart.legend(
            visible=visible,
            ohlc=False,
            percent=False,
            lines=lines,
            color=color,
            font_size=font_size,
            font_family=font_family,
            text=text,
            pane_index=pane_idx,
        )

    def _set_interval(self, df: pd.DataFrame):
        if not pd.api.types.is_datetime64_any_dtype(df["time"]):
            if pd.api.types.is_numeric_dtype(df["time"]):
                df["time"] = pd.to_datetime(df["time"], unit="s")
            else:
                df["time"] = pd.to_datetime(df["time"])
        common_interval = df["time"].diff().value_counts()
        if common_interval.empty:
            return
        self._interval = common_interval.index[0].total_seconds()

        units = [
            pd.Timedelta(
                microseconds=df["time"].dt.microsecond.value_counts().index[0]
            ),
            pd.Timedelta(seconds=df["time"].dt.second.value_counts().index[0]),
            pd.Timedelta(minutes=df["time"].dt.minute.value_counts().index[0]),
            pd.Timedelta(hours=df["time"].dt.hour.value_counts().index[0]),
            pd.Timedelta(days=df["time"].dt.day.value_counts().index[0]),
        ]
        self.offset = 0
        for value in units:
            value = value.total_seconds()
            if value == 0:
                continue
            elif value >= self._interval:
                break
            self.offset = value
            break

    @staticmethod
    def _format_labels(data, labels, index, exclude_lowercase):
        def rename(la, mapper):
            return [mapper[key] if key in mapper else key for key in la]

        if "date" not in labels and "time" not in labels:
            labels = labels.str.lower()
            if exclude_lowercase:
                labels = rename(labels, {exclude_lowercase.lower(): exclude_lowercase})
        if "date" in labels:
            labels = rename(labels, {"date": "time"})
        elif "time" not in labels:
            data["time"] = index
            labels = [*labels, "time"]
        return labels

    def _df_datetime_format(self, df: pd.DataFrame, exclude_lowercase=None):
        df = df.copy()
        df.columns = self._format_labels(df, df.columns, df.index, exclude_lowercase)
        self._set_interval(df)
        if not pd.api.types.is_datetime64_any_dtype(df["time"]):
            if pd.api.types.is_numeric_dtype(df["time"]):
                df["time"] = pd.to_datetime(df["time"], unit="s")
            else:
                df["time"] = pd.to_datetime(df["time"])
        df["time"] = df["time"].astype("datetime64[s]").astype("int64")
        return df

    def _series_datetime_format(self, series: pd.Series, exclude_lowercase=None):
        series = series.copy()
        series.index = self._format_labels(
            series, series.index, series.name, exclude_lowercase
        )
        series["time"] = self._single_datetime_format(series["time"])
        return series

    def _single_datetime_format(self, arg) -> float:
        if isinstance(
            arg, (str, int, float)
        ) or not pd.api.types.is_datetime64_any_dtype(arg):
            try:
                arg = pd.to_datetime(arg, unit="s")
            except ValueError:
                arg = pd.to_datetime(arg)
        arg = self._interval * (arg.timestamp() // self._interval) + self.offset
        return arg

    def set(self, df: Optional[pd.DataFrame] = None, format_cols: bool = True):
        if df is None or df.empty:
            self.run_script(f"{self.id}.series.setData([])")
            self.data = pd.DataFrame()
            return
        if format_cols:
            df = self._df_datetime_format(df, exclude_lowercase=self.name)
        if self.name:
            if self.name not in df:
                raise NameError(f'No column named "{self.name}".')
            df = df.rename(columns={self.name: "value"})
        self.data = df.copy()
        self._last_bar = df.iloc[-1]
        self.run_script(f"{self.id}.series.setData({js_data(df)}); ")

    def update(self, series: pd.Series, historicalUpdate: bool = False):
        series = self._series_datetime_format(series, exclude_lowercase=self.name)
        if self.name in series.index:
            series.rename({self.name: "value"}, inplace=True)
        if self._last_bar is not None and series["time"] != self._last_bar["time"]:
            self.data.loc[self.data.index[-1]] = self._last_bar
            self.data = pd.concat([self.data, series.to_frame().T], ignore_index=True)
        self._last_bar = series
        self.run_script(f"{self.id}.series.update({js_data(series)}, {jbool(historicalUpdate)});")

    def _update_markers(self):
        self.run_script(f'{self.id}.seriesMarkers.setMarkers({json.dumps(list(self.markers.values()))})')

    def marker_list(self, markers: list):
        """
        Creates multiple markers.\n
        :param markers: The list of markers to set. These should be in the format:\n
        [
            {"time": "2021-01-21", "position": "below", "shape": "circle", "color": "#2196F3", "text": ""},
            {"time": "2021-01-22", "position": "below", "shape": "circle", "color": "#2196F3", "text": ""},
            ...
        ]
        :return: a list of marker ids.
        """
        markers = markers.copy()
        marker_ids = []
        for marker in markers:
            marker_id = self.win._id_gen.generate()
            self.markers[marker_id] = {
                "time": self._single_datetime_format(marker["time"]),
                "position": marker_position(marker["position"]),
                "color": marker["color"],
                "shape": marker_shape(marker["shape"]),
                "text": marker["text"],
            }
            marker_ids.append(marker_id)
        self._update_markers()
        return marker_ids

    def marker(
        self,
        time: Optional[datetime] = None,
        position: MARKER_POSITION = "below",
        shape: MARKER_SHAPE = "arrow_up",
        color: str = "#2196F3",
        text: str = "",
    ) -> str:
        """
        Creates a new marker.\n
        :param time: Time location of the marker. If no time is given, it will be placed at the last bar.
        :param position: The position of the marker.
        :param color: The color of the marker (rgb, rgba or hex).
        :param shape: The shape of the marker.
        :param text: The text to be placed with the marker.
        :return: The id of the marker placed.
        """
        try:
            formatted_time = (
                self._last_bar["time"]
                if not time
                else self._single_datetime_format(time)
            )
        except TypeError:
            raise TypeError("Chart marker created before data was set.")
        marker_id = self.win._id_gen.generate()

        self.markers[marker_id] = {
            "time": int(formatted_time),
            "position": marker_position(position),
            "color": color,
            "shape": marker_shape(shape),
            "text": text,
        }
        self._update_markers()
        return marker_id

    def remove_marker(self, marker_id: str):
        """
        Removes the marker with the given id.\n
        """
        self.markers.pop(marker_id)
        self._update_markers()

    def horizontal_line(
        self,
        price: NUM,
        color: str = "rgb(122, 146, 202)",
        width: int = 2,
        style: LINE_STYLE = "solid",
        text: str = "",
        axis_label_visible: bool = True,
        func: Optional[Callable] = None,
    ) -> "HorizontalLine":
        """
        Creates a horizontal line at the given price.
        """
        return HorizontalLine(
            self, price, color, width, style, text, axis_label_visible, func
        )

    def trend_line(
        self,
        start_time: TIME,
        start_value: NUM,
        end_time: TIME,
        end_value: NUM,
        round: bool = False,
        line_color: str = "#1E80F0",
        width: int = 2,
        style: LINE_STYLE = "solid",
    ) -> TwoPointDrawing:
        return TrendLine(*locals().values())

    def box(
        self,
        start_time: TIME,
        start_value: NUM,
        end_time: TIME,
        end_value: NUM,
        round: bool = False,
        color: str = "#1E80F0",
        fill_color: str = "rgba(255, 255, 255, 0.2)",
        width: int = 2,
        style: LINE_STYLE = "solid",
    ) -> TwoPointDrawing:
        return Box(*locals().values())

    def ray_line(
        self,
        start_time: TIME,
        value: NUM,
        round: bool = False,
        color: str = "#1E80F0",
        width: int = 2,
        style: LINE_STYLE = "solid",
        text: str = "",
    ) -> RayLine:
        # TODO
        return RayLine(*locals().values())

    def vertical_line(
        self,
        time: TIME,
        color: str = "#1E80F0",
        width: int = 2,
        style: LINE_STYLE = "solid",
        text: str = "",
    ) -> VerticalLine:
        return VerticalLine(*locals().values())

    def clear_markers(self):
        """
        Clears the markers displayed on the data.\n
        """
        self.markers.clear()
        self._update_markers()

    def price_line(
        self, label_visible: bool = True, line_visible: bool = True, title: str = ""
    ):
        self.run_script(
            f"""
        {self.id}.series.applyOptions({{
            lastValueVisible: {jbool(label_visible)},
            priceLineVisible: {jbool(line_visible)},
            title: '{title}',
        }})"""
        )

    def precision(self, precision: int):
        """
        Sets the precision and minMove.\n
        :param precision: The number of decimal places.
        """
        min_move = 1 / (10**precision)
        self.run_script(
            f"""
        {self.id}.series.applyOptions({{
            priceFormat: {{precision: {precision}, minMove: {min_move}}}
        }})"""
        )
        self.num_decimals = precision

    def hide_data(self):
        self._toggle_data(False)

    def show_data(self):
        self._toggle_data(True)

    def _toggle_data(self, arg):
        self.run_script(
            f"""
        {self.id}.series.applyOptions({{visible: {jbool(arg)}}})
        if ('volumeSeries' in {self.id}) {self.id}.volumeSeries.applyOptions({{visible: {jbool(arg)}}})
        """
        )

    def vertical_span(
        self,
        start_time: Union[TIME, tuple, list],
        end_time: Optional[TIME] = None,
        color: str = "rgba(252, 219, 3, 0.2)",
        round: bool = False,
    ):
        """
        Creates a vertical line or span across the chart.\n
        Start time and end time can be used together, or end_time can be
        omitted and a single time or a list of times can be passed to start_time.
        """
        if round:
            start_time = self._single_datetime_format(start_time)
            end_time = self._single_datetime_format(end_time) if end_time else None
        return VerticalSpan(self, start_time, end_time, color)

    def attach_primitive(self, js_constructor_call: str) -> "AttachedPrimitive":
        """
        Attaches a JavaScript primitive to this series.
        :param js_constructor_call: A JavaScript expression that evaluates to a primitive object.
        :return: An AttachedPrimitive object with a .detach() method.
        """
        return AttachedPrimitive(self, js_constructor_call)

    # ── ISeriesApi additions ──────────────────────────────────────────────────

    def options(self) -> dict:
        """Returns the current series options as a dict (blocking)."""

        result = self.win.run_script_and_get(f"JSON.stringify({self.id}.series.options())")
        return json.loads(result) if isinstance(result, str) else {}

    def get_data(self) -> list:
        """Returns all series data as a list of dicts from JS (blocking)."""

        result = self.win.run_script_and_get(f"JSON.stringify({self.id}.series.data())")
        return json.loads(result) if isinstance(result, str) else []

    def data_by_index(
        self,
        logical_index: int,
        mismatch_direction: "Literal['nearest_left', 'nearest_right', None]" = None,
    ) -> dict:
        """Returns the data point at *logical_index* (blocking)."""

        dir_map = {'nearest_left': -1, 'nearest_right': 1}
        dir_arg = dir_map.get(mismatch_direction, 0) if mismatch_direction else 0
        result = self.win.run_script_and_get(
            f"JSON.stringify({self.id}.series.dataByIndex({int(logical_index)}, {dir_arg}))"
        )
        return json.loads(result) if isinstance(result, str) else {}

    def price_to_coordinate(self, price: float) -> Optional[float]:
        """Converts a price to a y-coordinate (blocking, synchronous)."""
        result = self.win.run_script_and_get(
            f"{self.id}.series.priceToCoordinate({float(price)})"
        )
        return float(result) if result not in (None, 'null', 'undefined') else None

    def coordinate_to_price(self, coordinate: float) -> Optional[float]:
        """Converts a y-coordinate to a price (blocking, synchronous)."""
        result = self.win.run_script_and_get(
            f"{self.id}.series.coordinateToPrice({float(coordinate)})"
        )
        return float(result) if result not in (None, 'null', 'undefined') else None

    def bars_in_logical_range(self, from_index: int, to_index: int) -> Optional[dict]:
        """Returns bars info for the given logical index range (blocking)."""

        result = self.win.run_script_and_get(
            f"JSON.stringify({self.id}.series.barsInLogicalRange({{from: {int(from_index)}, to: {int(to_index)}}}))".replace(
                "\\\"from\\\"", "from").replace("\\\"to\\\"", "to")
        )
        return json.loads(result) if isinstance(result, str) else None

    def series_type(self) -> str:
        """Returns the series type string (blocking)."""
        result = self.win.run_script_and_get(f"{self.id}.series.seriesType()")
        return str(result) if result else ''

    def last_value_data(self, global_last: bool = True) -> Optional[dict]:
        """Returns data about the last visible value (blocking)."""

        result = self.win.run_script_and_get(
            f"JSON.stringify({self.id}.series.lastValueData({jbool(global_last)}))"
        )
        return json.loads(result) if isinstance(result, str) else None

    def series_order(self) -> int:
        """Returns the Z-order of this series within its pane (blocking)."""
        result = self.win.run_script_and_get(f"{self.id}.series.seriesOrder()")
        return int(result) if result is not None else 0

    def set_series_order(self, order: int):
        """Sets the Z-order of this series within its pane."""
        self.run_script(f"{self.id}.series.setSeriesOrder({int(order)})")

    def move_to_pane(self, pane_index: int | None = None):
        """Moves this series to the pane at *pane_index* (requires window open when pane_index is None)."""
        if pane_index is None:
            self.run_script(f"{self.id}.series.moveToPane()")
            self.pane_index = int(self.win.run_script_and_get(
                f"{self._chart.id}.chart.panes().indexOf({self.id}.series.getPane())"
            ))
        else:
            self.run_script(f"{self.id}.series.moveToPane({int(pane_index)})")
            self.pane_index = pane_index

    def get_pane(self) -> "Pane":
        """Returns the ``Pane`` for the pane this series lives on (blocking)."""
        idx = int(self.win.run_script_and_get(
            f"{self._chart.id}.chart.panes().indexOf({self.id}.series.getPane())"
        ))
        return Pane(self._chart, idx)

    def subscribe_data_changed(self, func: Callable):
        """
        Subscribes to data changes on this series.
        :param func: Callable receiving this series as its first argument.
        """
        salt = self.id.replace('window.', '')
        handler_id = f'data_changed_{salt}'
        self._data_changed_handler_id = handler_id

        def _wrapper(*_args):
            if inspect.iscoroutinefunction(func):
                asyncio.create_task(func(self))
            else:
                func(self)

        self.win.handlers[handler_id] = _wrapper
        self.run_script(f"""
            if (typeof {self.id}._dataChangedCb !== 'undefined') {{
                {self.id}.series.unsubscribeDataChanged({self.id}._dataChangedCb);
            }}
            {self.id}._dataChangedCb = () => window.callbackFunction('{handler_id}_~_');
            {self.id}.series.subscribeDataChanged({self.id}._dataChangedCb);
        null""")

    def unsubscribe_data_changed(self):
        """Unsubscribes from data change events on this series."""
        if self._data_changed_handler_id:
            self.win.handlers.pop(self._data_changed_handler_id, None)
            self._data_changed_handler_id = None
        self.run_script(f"""
            if (typeof {self.id}._dataChangedCb !== 'undefined') {{
                {self.id}.series.unsubscribeDataChanged({self.id}._dataChangedCb);
                delete {self.id}._dataChangedCb;
            }}
        null""")

    def price_lines(self) -> list:
        """Returns all price lines attached to this series as a list of dicts (blocking)."""

        result = self.win.run_script_and_get(
            f"JSON.stringify({self.id}.series.priceLines().map(pl => pl.options()))"
        )
        return json.loads(result) if isinstance(result, str) else []


class Line(SeriesCommon):
    def __init__(
        self,
        chart,
        name,
        color,
        style,
        type,
        width,
        price_line,
        price_label,
        price_scale_id=None,
        crosshair_marker=True,
        last_price_animation: LAST_PRICE_ANIMATION_MODE = 'disabled',
        pane_index: int = None,
    ):
        super().__init__(chart, name, pane_index)
        self.color = color

        self.run_script(
            f'''
            {self.id} = {self._chart.id}.createLineSeries(
                "{name}",
                {{
                    color: '{color}',
                    lineStyle: {as_enum(style, LINE_STYLE)},
                    lineType: {as_enum(type, LINE_TYPE)},
                    lineWidth: {width},
                    lastValueVisible: {jbool(price_label)},
                    priceLineVisible: {jbool(price_line)},
                    crosshairMarkerVisible: {jbool(crosshair_marker)},
                    priceScaleId: {f'"{price_scale_id}"' if price_scale_id else 'undefined'},
                    lastPriceAnimation: {as_enum(last_price_animation, LAST_PRICE_ANIMATION_MODE)},
                    {"""autoscaleInfoProvider: () => ({
                            priceRange: {
                                minValue: 1_000_000_000,
                                maxValue: 0,
                            },
                        }),
                    """ if chart._scale_candles_only else ''}
                    
                }},
                {f'{pane_index},' if pane_index is not None else '0'}
            )
        null'''
        )

    # def _set_trend(self, start_time, start_value, end_time, end_value, ray=False, round=False):
    #     if round:
    #         start_time = self._single_datetime_format(start_time)
    #         end_time = self._single_datetime_format(end_time)
    #     else:
    #         start_time, end_time = pd.to_datetime((start_time, end_time)).astype('int64') // 10 ** 9

    #     self.run_script(f'''
    #     {self._chart.id}.chart.timeScale().applyOptions({{shiftVisibleRangeOnNewBar: false}})
    #     {self.id}.series.setData(
    #         calculateTrendLine({start_time}, {start_value}, {end_time}, {end_value},
    #                             {self._chart.id}, {jbool(ray)}))
    #     {self._chart.id}.chart.timeScale().applyOptions({{shiftVisibleRangeOnNewBar: true}})
    #     ''')

    def delete(self):
        """
        Irreversibly deletes the line, as well as the object that contains the line.
        """
        self._chart._lines.remove(self) if self in self._chart._lines else None
        pane_idx = self.pane_index if self.pane_index is not None else 0
        self.run_script(
            f"""
            var _leg = {self._chart.id}.legends.get({int(pane_idx)});
            if (_leg) {{
                {self.id}legendItem = _leg._lines.find((line) => line.series == {self.id}.series);
                _leg._lines = _leg._lines.filter((item) => item != {self.id}legendItem);
                if ({self.id}legendItem) _leg.div.removeChild({self.id}legendItem.row);
                delete {self.id}legendItem;
            }}
            {self._chart.id}.chart.removeSeries({self.id}.series);
            delete {self.id};
        """
        )


class Area(SeriesCommon):
    def __init__(
        self,
        chart,
        name,
        top_color,
        bottom_color,
        line_color,
        line_width,
        price_line,
        price_label,
        price_scale_id=None,
        crosshair_marker=True,
        last_price_animation: LAST_PRICE_ANIMATION_MODE = 'disabled',
        pane_index: int = None,
    ):
        super().__init__(chart, name, pane_index)
        self.run_script(
            f'''
            {self.id} = {self._chart.id}.createAreaSeries(
                "{name}",
                {{
                    topColor: '{top_color}',
                    bottomColor: '{bottom_color}',
                    lineColor: '{line_color}',
                    lineWidth: {line_width},
                    lastValueVisible: {jbool(price_label)},
                    priceLineVisible: {jbool(price_line)},
                    crosshairMarkerVisible: {jbool(crosshair_marker)},
                    priceScaleId: {f'"{price_scale_id}"' if price_scale_id else 'undefined'},
                    lastPriceAnimation: {as_enum(last_price_animation, LAST_PRICE_ANIMATION_MODE)},
                }},
                {pane_index if pane_index is not None else 0}
            )
        null'''
        )

    _AREA_COLOR_RENAME = {
        'line_color': 'lineColor',
        'top_color': 'topColor',
        'bottom_color': 'bottomColor',
    }

    def set(self, df: Optional[pd.DataFrame] = None, format_cols: bool = True):
        """
        Sets the area series data. Accepts optional per-point color columns:
        ``line_color`` / ``lineColor``, ``top_color`` / ``topColor``,
        ``bottom_color`` / ``bottomColor``.
        """
        if df is not None and not df.empty:
            df = df.rename(columns=self._AREA_COLOR_RENAME)
        super().set(df, format_cols)

    def update(self, series: pd.Series, historicalUpdate: bool = False):
        """
        Updates the area series. Accepts optional per-point color keys:
        ``line_color`` / ``lineColor``, ``top_color`` / ``topColor``,
        ``bottom_color`` / ``bottomColor``.
        """
        series = series.rename(self._AREA_COLOR_RENAME)
        super().update(series, historicalUpdate)

    def delete(self):
        """
        Irreversibly deletes the area series.
        """
        self._chart._lines.remove(self) if self in self._chart._lines else None
        pane_idx = self.pane_index if self.pane_index is not None else 0
        self.run_script(
            f"""
            var _leg = {self._chart.id}.legends.get({int(pane_idx)});
            if (_leg) {{
                {self.id}legendItem = _leg._lines.find((line) => line.series == {self.id}.series);
                _leg._lines = _leg._lines.filter((item) => item != {self.id}legendItem);
                if ({self.id}legendItem) _leg.div.removeChild({self.id}legendItem.row);
                delete {self.id}legendItem;
            }}
            {self._chart.id}.chart.removeSeries({self.id}.series);
            delete {self.id};
        """
        )


class AttachedPrimitive(_PaneBase):
    """
    Wraps a JavaScript series primitive attached via series.attachPrimitive().
    """

    def __init__(self, series: "SeriesCommon", js_constructor_call: str):
        super().__init__(series.win)
        self._series = series
        self.run_script(
            f"""
            {self.id} = {js_constructor_call};
            {series.id}.series.attachPrimitive({self.id});
        null"""
        )

    def detach(self):
        """Detaches the primitive from the series."""
        self.run_script(f"{self._series.id}.series.detachPrimitive({self.id})")

    def update_options(self, options: dict):
        """Calls applyOptions on the primitive."""
        self.run_script(f"{self.id}.applyOptions({js_json(options)})")


class UpDownMarkers(_PaneBase):
    """
    Attaches an up/down marker primitive to a series using LWC v5's
    createUpDownMarkers API.
    """

    def __init__(
        self,
        chart,
        series: "SeriesCommon",
        up_color: str = "#26a69a",
        down_color: str = "#ef5350",
    ):
        super().__init__(chart.win)
        self._series = series
        self.run_script(
            f"""
            {self.id} = LightweightCharts.createUpDownMarkers(
                {series.id}.series,
                {{
                    positiveColor: '{up_color}',
                    negativeColor: '{down_color}',
                }}
            )
        null"""
        )

    def detach(self):
        """Detaches the up/down markers from the series."""
        self.run_script(f"{self.id}.detach()")


class Pane(_PaneBase):
    """
    Python wrapper for the LWC IPaneApi. Represents a single chart pane.

    .. note::
        ``Pane`` instances become stale after structural pane changes
        (``remove_pane``, ``swap_panes``). Re-call ``chart.panes()`` after
        such operations.
    """

    def __init__(self, chart: "AbstractChart", pane_index: int):
        super().__init__(chart.win)
        self._chart = chart
        self._pane_index = pane_index

    def _pane_expr(self) -> str:
        return f"{self._chart.id}.chart.panes()[{self._pane_index}]"

    def get_height(self) -> int:
        """Returns the pane height in pixels (blocking)."""
        return int(self.win.run_script_and_get(f"{self._pane_expr()}.getHeight()"))

    def set_height(self, height: int):
        """Sets the pane height in pixels."""
        self.run_script(f"{self._pane_expr()}.setHeight({int(height)})")

    def move_to(self, pane_index: int):
        """Reorders this pane to the given index."""
        self.run_script(f"{self._pane_expr()}.moveTo({int(pane_index)})")
        self._pane_index = pane_index

    def pane_index(self) -> int:
        """Returns the current pane index (uses cached value)."""
        return self._pane_index

    def get_series(self) -> list:
        """
        Returns the list of ``SeriesCommon`` objects on this pane that are
        tracked in the parent chart's series registry.
        """
        return [s for s in self._chart._series_registry if s.pane_index == self._pane_index]

    def attach_primitive(self, js_constructor_call: str) -> "AttachedPanePrimitive":
        """
        Attaches a JavaScript primitive at the pane level.
        :param js_constructor_call: JS expression evaluating to a primitive object.
        :return: An ``AttachedPanePrimitive`` instance.
        """
        return AttachedPanePrimitive(self, js_constructor_call)

    def detach_primitive(self, primitive: "AttachedPanePrimitive"):
        """Detaches a previously attached pane primitive."""
        primitive.detach()

    def price_scale(self, price_scale_id: str):
        """Returns a JS price scale reference expression (not a Python object)."""
        self.run_script(
            f"{self._pane_expr()}.priceScale('{price_scale_id}')"
        )

    def set_preserve_empty_pane(self, preserve: bool):
        """Sets whether this pane is preserved when all its series are removed."""
        self.run_script(
            f"{self._pane_expr()}.setPreserveEmptyPane({jbool(preserve)})"
        )

    def preserve_empty_pane(self) -> bool:
        """Returns whether the empty-pane preservation flag is set (blocking)."""
        result = self.win.run_script_and_get(f"{self._pane_expr()}.preserveEmptyPane()")
        return result is True or result == 'true'

    def get_stretch_factor(self) -> float:
        """Returns the relative height factor of this pane (blocking)."""
        return float(self.win.run_script_and_get(f"{self._pane_expr()}.getStretchFactor()"))

    def set_stretch_factor(self, factor: float):
        """Sets the relative height factor of this pane."""
        self.run_script(f"{self._pane_expr()}.setStretchFactor({float(factor)})")


class AttachedPanePrimitive(_PaneBase):
    """Wraps a JavaScript primitive attached at the pane level."""

    def __init__(self, pane: Pane, js_constructor_call: str):
        super().__init__(pane.win)
        self._pane = pane
        self.run_script(
            f"""
            {self.id} = {js_constructor_call};
            {pane._pane_expr()}.attachPrimitive({self.id});
        null"""
        )

    def detach(self):
        """Detaches this primitive from the pane."""
        self.run_script(f"{self._pane._pane_expr()}.detachPrimitive({self.id})")


class Histogram(SeriesCommon):
    def __init__(
        self,
        chart,
        name,
        color,
        price_line,
        price_label,
        scale_margin_top,
        scale_margin_bottom,
        pane_index: int = None,
        price_scale_id: Optional[str] = None,
    ):
        super().__init__(chart, name, pane_index)
        self.color = color
        self.run_script(
            f"""
        {self.id} = {chart.id}.createHistogramSeries(
            "{name}",
            {{
                color: '{color}',
                lastValueVisible: {jbool(price_label)},
                priceLineVisible: {jbool(price_line)},
                priceScaleId: '{price_scale_id or self.id}',
                priceFormat: {{type: "volume"}},
            }},
            {f'{pane_index}' if pane_index is not None else '0'}
        )
        {self.id}.series.priceScale().applyOptions({{
            scaleMargins: {{top:{scale_margin_top}, bottom: {scale_margin_bottom}}}
        }})"""
        )

    def delete(self):
        """
        Irreversibly deletes the histogram.
        """
        pane_idx = self.pane_index if self.pane_index is not None else 0
        self.run_script(
            f"""
            var _leg = {self._chart.id}.legends.get({int(pane_idx)});
            if (_leg) {{
                {self.id}legendItem = _leg._lines.find((line) => line.series == {self.id}.series);
                _leg._lines = _leg._lines.filter((item) => item != {self.id}legendItem);
                if ({self.id}legendItem) _leg.div.removeChild({self.id}legendItem.row);
                delete {self.id}legendItem;
            }}
            {self._chart.id}.chart.removeSeries({self.id}.series);
            delete {self.id};
        """
        )

    def scale(self, scale_margin_top: float = 0.0, scale_margin_bottom: float = 0.0):
        self.run_script(
            f"""
        {self.id}.series.priceScale().applyOptions({{
            scaleMargins: {{top: {scale_margin_top}, bottom: {scale_margin_bottom}}}
        }})"""
        )


class Candlestick(SeriesCommon):
    def __init__(self, chart: "AbstractChart"):
        super().__init__(chart)
        self._volume_up_color = "rgba(83,141,131,0.8)"
        self._volume_down_color = "rgba(200,127,130,0.8)"

        self.candle_data = pd.DataFrame()

        # self.run_script(f'{self.id}.makeCandlestickSeries()')

    def set(self, df: Optional[pd.DataFrame] = None, keep_drawings=False):
        """
        Sets the initial data for the chart.\n
        :param df: columns: date/time, open, high, low, close, volume (if volume enabled).
        :param keep_drawings: keeps any drawings made through the toolbox. Otherwise, they will be deleted.
        """
        if df is None or df.empty:
            self.run_script(f"{self.id}.series.setData([])")
            self.run_script(f"{self.id}.volumeSeries.setData([])")
            self.candle_data = pd.DataFrame()
            return
        df = self._df_datetime_format(df)
        self.candle_data = df.copy()
        self._last_bar = df.iloc[-1]
        self.run_script(f"{self.id}.series.setData({js_data(df)})")

        if "volume" not in df:
            return
        volume = df.drop(columns=["open", "high", "low", "close"]).rename(
            columns={"volume": "value"}
        )
        volume["color"] = self._volume_down_color
        volume.loc[df["close"] > df["open"], "color"] = self._volume_up_color
        self.run_script(f"{self.id}.volumeSeries.setData({js_data(volume)})")

        for line in self._lines:
            if line.name not in df.columns:
                continue
            line.set(df[["time", line.name]], format_cols=False)
        # set autoScale to true in case the user has dragged the price scale
        self.run_script(
            f"""
            if (!{self.id}.chart.priceScale("right")?.options?.autoScale) // precision: 2, 
                {self.id}.chart.priceScale("right").applyOptions({{autoScale: true}})
        """
        )
        # TODO keep drawings doesn't work consistenly w
        if keep_drawings:
            self.run_script(
                f"{self._chart.id}.toolBox?._drawingTool.repositionOnTime()"
            )
        else:
            self.run_script(f"{self._chart.id}.toolBox?.clearDrawings()")

    def update(self, series: pd.Series, _from_tick=False):
        """
        Updates the data from a bar;
        if series['time'] is the same time as the last bar, the last bar will be overwritten.\n
        :param series: labels: date/time, open, high, low, close, volume (if using volume).
        """
        series = self._series_datetime_format(series) if not _from_tick else series
        if series["time"] != self._last_bar["time"]:
            self.candle_data.loc[self.candle_data.index[-1]] = self._last_bar
            self.candle_data = pd.concat(
                [self.candle_data, series.to_frame().T], ignore_index=True
            )
            self._chart.events.new_bar._emit(self)

        self._last_bar = series
        self.run_script(f"{self.id}.series.update({js_data(series)})")
        if "volume" not in series:
            return
        volume = series.drop(["open", "high", "low", "close"]).rename(
            {"volume": "value"}
        )
        volume["color"] = (
            self._volume_up_color
            if series["close"] > series["open"]
            else self._volume_down_color
        )
        self.run_script(f"{self.id}.volumeSeries.update({js_data(volume)})")

    def update_from_tick(self, series: pd.Series, cumulative_volume: bool = False):
        """
        Updates the data from a tick.\n
        :param series: labels: date/time, price, volume (if using volume).
        :param cumulative_volume: Adds the given volume onto the latest bar.
        """
        series = self._series_datetime_format(series)
        if series["time"] < self._last_bar["time"]:
            raise ValueError(
                f'Trying to update tick of time "{pd.to_datetime(series["time"])}", which occurs before the last bar time of "{pd.to_datetime(self._last_bar["time"])}".'
            )
        bar = pd.Series(dtype="float64")
        if series["time"] == self._last_bar["time"]:
            bar = self._last_bar
            bar["high"] = max(self._last_bar["high"], series["price"])
            bar["low"] = min(self._last_bar["low"], series["price"])
            bar["close"] = series["price"]
            if "volume" in series:
                if cumulative_volume:
                    bar["volume"] += series["volume"]
                else:
                    bar["volume"] = series["volume"]
        else:
            for key in ("open", "high", "low", "close"):
                bar[key] = series["price"]
            bar["time"] = series["time"]
            if "volume" in series:
                bar["volume"] = series["volume"]
        self.update(bar, _from_tick=True)

    def price_scale(
        self,
        auto_scale: bool = True,
        mode: PRICE_SCALE_MODE = "normal",
        invert_scale: bool = False,
        align_labels: bool = True,
        scale_margin_top: float = 0.2,
        scale_margin_bottom: float = 0.2,
        border_visible: bool = False,
        border_color: Optional[str] = None,
        text_color: Optional[str] = None,
        entire_text_only: bool = False,
        visible: bool = True,
        ticks_visible: bool = False,
        minimum_width: int = 0,
    ):
        self.run_script(
            f"""
            {self.id}.series.priceScale().applyOptions({{
                autoScale: {jbool(auto_scale)},
                mode: {as_enum(mode, PRICE_SCALE_MODE)},
                invertScale: {jbool(invert_scale)},
                alignLabels: {jbool(align_labels)},
                scaleMargins: {{top: {scale_margin_top}, bottom: {scale_margin_bottom}}},
                borderVisible: {jbool(border_visible)},
                {f'borderColor: "{border_color}",' if border_color else ''}
                {f'textColor: "{text_color}",' if text_color else ''}
                entireTextOnly: {jbool(entire_text_only)},
                visible: {jbool(visible)},
                ticksVisible: {jbool(ticks_visible)},
                minimumWidth: {minimum_width}
            }})"""
        )

    def candle_style(
        self,
        up_color: str = "rgba(39, 157, 130, 100)",
        down_color: str = "rgba(200, 97, 100, 100)",
        wick_visible: bool = True,
        border_visible: bool = True,
        border_up_color: str = "",
        border_down_color: str = "",
        wick_up_color: str = "",
        wick_down_color: str = "",
    ):
        """
        Candle styling for each of its parts.\n
        If only `up_color` and `down_color` are passed, they will color all parts of the candle.
        """
        border_up_color = border_up_color if border_up_color else up_color
        border_down_color = border_down_color if border_down_color else down_color
        wick_up_color = wick_up_color if wick_up_color else up_color
        wick_down_color = wick_down_color if wick_down_color else down_color
        self.run_script(f"{self.id}.series.applyOptions({js_json(locals())})")

    def volume_config(
        self,
        scale_margin_top: float = 0.8,
        scale_margin_bottom: float = 0.0,
        up_color="rgba(83,141,131,0.8)",
        down_color="rgba(200,127,130,0.8)",
    ):
        """
        Configure volume settings.\n
        Numbers for scaling must be greater than 0 and less than 1.\n
        Volume colors must be applied prior to setting/updating the bars.\n
        """
        self._volume_up_color = up_color if up_color else self._volume_up_color
        self._volume_down_color = down_color if down_color else self._volume_down_color
        self.run_script(
            f"""
        {self.id}.volumeSeries.priceScale().applyOptions({{
            scaleMargins: {{
            top: {scale_margin_top},
            bottom: {scale_margin_bottom},
            }}
        }})"""
        )


class AbstractChart(Candlestick, _PaneBase):
    def __init__(
        self,
        window: Window,
        width: float = 1.0,
        height: float = 1.0,
        scale_candles_only: bool = False,
        toolbox: bool = False,
        autosize: bool = True,
        position: FLOAT = "left",
    ):
        _PaneBase.__init__(self, window)

        self._lines = []
        self._series_registry: List["SeriesCommon"] = []
        self._scale_candles_only = scale_candles_only
        self._width = width
        self._height = height
        self.events: Events = Events(self)

        from lightweight_charts.polygon import PolygonAPI

        self.polygon: PolygonAPI = PolygonAPI(self)

        self.run_script(
            f'{self.id} = new Lib.Handler("{self.id}", {width}, {height}, "{position}", {jbool(autosize)})'
        )

        Candlestick.__init__(self, self)

        self.topbar: TopBar = TopBar(self)
        if toolbox:
            self.toolbox: ToolBox = ToolBox(self)

    def fit(self):
        """
        Fits the maximum amount of the chart data within the viewport.
        """
        self.run_script(f"{self.id}.chart.timeScale().fitContent()")

    def create_line(
        self,
        name: str = "",
        color: str = "rgba(214, 237, 255, 0.6)",
        style: LINE_STYLE = "solid",
        type: LINE_TYPE = "simple",
        width: int = 2,
        price_line: bool = True,
        price_label: bool = True,
        price_scale_id: Optional[str] = None,
        pane_index: int = None,
        last_price_animation: str = 'disabled',
    ) -> Line:
        """
        Creates and returns a Line object.
        """
        self._lines.append(
            Line(
                self,
                name,
                color,
                style,
                type,
                width,
                price_line,
                price_label,
                price_scale_id,
                pane_index=pane_index,
                last_price_animation=last_price_animation,
            )
        )
        return self._lines[-1]

    def create_area(
        self,
        name: str = "",
        top_color: str = "rgba(33, 150, 243, 0.4)",
        bottom_color: str = "rgba(33, 150, 243, 0.0)",
        line_color: str = "#2196F3",
        line_width: int = 2,
        price_line: bool = True,
        price_label: bool = True,
        pane_index: int = None,
    ) -> Area:
        """
        Creates and returns an Area series object.
        """
        return Area(
            self,
            name,
            top_color,
            bottom_color,
            line_color,
            line_width,
            price_line,
            price_label,
            pane_index=pane_index,
        )

    def create_histogram(
        self,
        name: str = "",
        color: str = "rgba(214, 237, 255, 0.6)",
        price_line: bool = True,
        price_label: bool = True,
        scale_margin_top: float = 0.0,
        scale_margin_bottom: float = 0.0,
        pane_index: int = 0,
        price_scale_id: Optional[str] = None,
    ) -> Histogram:
        """
        Creates and returns a Histogram object.
        """
        return Histogram(
            self,
            name,
            color,
            price_line,
            price_label,
            scale_margin_top,
            scale_margin_bottom,
            pane_index,
            price_scale_id,
        )

    def lines(self) -> List[Line]:
        """
        Returns all lines for the chart.
        """
        return self._lines.copy()

    def set_visible_range(self, start_time: TIME, end_time: TIME):
        self.run_script(
            f"""
        {self.id}.chart.timeScale().setVisibleRange({{
            from: {pd.to_datetime(start_time).timestamp()},
            to: {pd.to_datetime(end_time).timestamp()}
        }})
        """
        )

    def resize(self, width: Optional[float] = None, height: Optional[float] = None):
        """
        Resizes the chart within the window.
        Dimensions should be given as a float between 0 and 1.
        """
        self._width = width if width is not None else self._width
        self._height = height if height is not None else self._height
        self.run_script(
            f"""
        {self.id}.scale.width = {self._width}
        {self.id}.scale.height = {self._height}
        {self.id}.reSize()
        """
        )

    def time_scale(
        self,
        right_offset: int = 0,
        min_bar_spacing: float = 0.5,
        visible: bool = True,
        time_visible: bool = True,
        seconds_visible: bool = False,
        border_visible: bool = True,
        border_color: Optional[str] = None,
    ):
        """
        Options for the timescale of the chart.
        """
        self.run_script(
            f"""{self.id}.chart.applyOptions({{timeScale: {js_json(locals())}}})"""
        )

    def layout(
        self,
        background_color: str = "#000000",
        text_color: Optional[str] = None,
        font_size: Optional[int] = None,
        font_family: Optional[str] = None,
    ):
        """
        Global layout options for the chart.
        """
        self.run_script(
            f"""
            document.getElementById('container').style.backgroundColor = '{background_color}'
            {self.id}.chart.applyOptions({{
            layout: {{
                background: {{color: "{background_color}"}},
                {f'textColor: "{text_color}",' if text_color else ''}
                {f'fontSize: {font_size},' if font_size else ''}
                {f'fontFamily: "{font_family}",' if font_family else ''}
            }}}})"""
        )

    def grid(
        self,
        vert_enabled: bool = True,
        horz_enabled: bool = True,
        color: str = "rgba(29, 30, 38, 5)",
        style: LINE_STYLE = "solid",
    ):
        """
        Grid styling for the chart.
        """
        self.run_script(
            f"""
           {self.id}.chart.applyOptions({{
           grid: {{
               vertLines: {{
                   visible: {jbool(vert_enabled)},
                   color: "{color}",
                   style: {as_enum(style, LINE_STYLE)},
               }},
               horzLines: {{
                   visible: {jbool(horz_enabled)},
                   color: "{color}",
                   style: {as_enum(style, LINE_STYLE)},
               }},
           }}
           }})"""
        )

    def crosshair(
        self,
        mode: CROSSHAIR_MODE = "normal",
        vert_visible: bool = True,
        vert_width: int = 1,
        vert_color: Optional[str] = None,
        vert_style: LINE_STYLE = "large_dashed",
        vert_label_background_color: str = "rgb(46, 46, 46)",
        horz_visible: bool = True,
        horz_width: int = 1,
        horz_color: Optional[str] = None,
        horz_style: LINE_STYLE = "large_dashed",
        horz_label_background_color: str = "rgb(55, 55, 55)",
    ):
        """
        Crosshair formatting for its vertical and horizontal axes.
        """
        self.run_script(
            f"""
        {self.id}.chart.applyOptions({{
            crosshair: {{
                mode: {as_enum(mode, CROSSHAIR_MODE)},
                vertLine: {{
                    visible: {jbool(vert_visible)},
                    width: {vert_width},
                    {f'color: "{vert_color}",' if vert_color else ''}
                    style: {as_enum(vert_style, LINE_STYLE)},
                    labelBackgroundColor: "{vert_label_background_color}"
                }},
                horzLine: {{
                    visible: {jbool(horz_visible)},
                    width: {horz_width},
                    {f'color: "{horz_color}",' if horz_color else ''}
                    style: {as_enum(horz_style, LINE_STYLE)},
                    labelBackgroundColor: "{horz_label_background_color}"
                }}
            }}
        }})"""
        )

    def watermark(self, text: str, font_size: int = 44, color: str = 'rgba(180, 180, 200, 0.5)'):
        """
        Adds a watermark to the chart.
        """
        self.run_script(f'''{self._chart.id}.createWatermark('{text}', {font_size}, '{color}')''')

    def legend(
        self,
        visible: bool = False,
        ohlc: bool = True,
        percent: bool = True,
        lines: bool = True,
        color: str = "rgb(191, 195, 203)",
        font_size: int = 11,
        font_family: str = "Monaco",
        text: str = "",
        color_based_on_candle: bool = False,
        pane_index: int = 0,
    ):
        """
        Configures the legend of the chart.
        :param pane_index: Which pane's legend to configure (default 0).
        """
        l_id = f"{self.id}.getOrCreateLegend({int(pane_index)})"
        if not visible:
            self.run_script(
                f"""
            {l_id}.div.style.display = "none"
            {l_id}.ohlcEnabled = false
            {l_id}.percentEnabled = false
            {l_id}.linesEnabled = false
            """
            )
            return
        self.run_script(
            f"""
        {l_id}.div.style.display = 'flex'
        {l_id}.ohlcEnabled = {jbool(ohlc)}
        {l_id}.percentEnabled = {jbool(percent)}
        {l_id}.linesEnabled = {jbool(lines)}
        {l_id}.colorBasedOnCandle = {jbool(color_based_on_candle)}
        {l_id}.div.style.color = '{color}'
        {l_id}.div.style.fontSize = '{font_size}px'
        {l_id}.div.style.fontFamily = '{font_family}'
        {l_id}.text.innerText = '{text}'
        """
        )

    def spinner(self, visible):
        self.run_script(
            f"{self.id}.spinner.style.display = '{'block' if visible else 'none'}'"
        )

    def hotkey(
        self,
        modifier_key: Literal["ctrl", "alt", "shift", "meta", None],
        keys: Union[str, tuple, int],
        func: Callable,
    ):
        if not isinstance(keys, tuple):
            keys = (keys,)
        for key in keys:
            key = str(key)
            if key.isalnum() and len(key) == 1:
                key_code = f"Digit{key}" if key.isdigit() else f"Key{key.upper()}"
                key_condition = f'event.code === "{key_code}"'
            else:
                key_condition = f'event.key === "{key}"'
            if modifier_key is not None:
                key_condition += f"&& event.{modifier_key}Key"

            self.run_script(
                f"""
                    {self.id}.commandFunctions.unshift((event) => {{
                        if ({key_condition}) {{
                            event.preventDefault()
                            window.callbackFunction(`{modifier_key, keys}_~_{key}`)
                            return true
                        }}
                        else return false
                    }})"""
            )
        self.win.handlers[f"{modifier_key, keys}"] = func

    def create_table(
        self,
        width: NUM,
        height: NUM,
        headings: tuple,
        widths: Optional[tuple] = None,
        alignments: Optional[tuple] = None,
        position: FLOAT = "left",
        draggable: bool = False,
        background_color: str = "#121417",
        border_color: str = "rgb(70, 70, 70)",
        border_width: int = 1,
        heading_text_colors: Optional[tuple] = None,
        heading_background_colors: Optional[tuple] = None,
        return_clicked_cells: bool = False,
        func: Optional[Callable] = None,
    ) -> Table:
        args = locals()
        del args["self"]
        return self.win.create_table(*args.values())

    def screenshot(self) -> bytes:
        """
        Takes a screenshot. This method can only be used after the chart window is visible.
        :return: a bytes object containing a screenshot of the chart.
        """
        serial_data = self.win.run_script_and_get(
            f"{self.id}.chart.takeScreenshot().toDataURL()"
        )
        return b64decode(serial_data.split(",")[1])

    def resize_pane(self, pane_index: int, height: int):
        self.run_script(
            f"""
            if ({self.id}.chart.panes().length > {pane_index}) {{
                {self.id}.chart.panes()[{pane_index}].setHeight({height});
            }}
        """
        )

    def remove_pane(self, pane_index: int):
        self.run_script(
            f"""
                    {self.id}.chart.removePane({pane_index});
            """
        )

    def add_pane(self, height: Optional[int] = None) -> None:
        """
        Adds a new pane to the chart.
        :param height: Optional height in pixels for the new pane.
        """
        self.run_script(
            f"{self.id}.chart.addPane({height if height is not None else ''})"
        )

    def get_pane_count(self) -> int:
        """
        Returns the current number of panes in the chart.
        """
        return int(self.win.run_script_and_get(f"{self.id}.chart.panes().length"))

    def panes(self) -> "List[Pane]":
        """
        Returns a list of ``Pane`` objects, one per pane.
        The pane count is fetched from JS once; the list is rebuilt on each call.
        """
        count = int(self.win.run_script_and_get(f"{self.id}.chart.panes().length"))
        return [Pane(self, i) for i in range(count)]

    def swap_panes(self, first: int, second: int):
        """Swaps the panes at *first* and *second* indices."""
        self.run_script(f"{self.id}.chart.swapPanes({int(first)}, {int(second)})")

    # ── IChartApi additions ───────────────────────────────────────────────────

    def auto_size_active(self) -> bool:
        """Returns whether autosize is currently active (blocking)."""
        result = self.win.run_script_and_get(f"{self.id}.chart.autoSizeActive()")
        return result is True or result == 'true'

    def subscribe_dbl_click(self, func: Callable):
        """
        Subscribes to double-click events on the chart.
        :param func: Callable receiving ``(chart, time, price)`` arguments.
        """
        salt = self.id.replace('window.', '')
        handler_id = f'dbl_click_{salt}'

        def _wrapper(chart, *args):
            parsed = [float(a) if a != 'null' else None for a in args]
            if inspect.iscoroutinefunction(func):
                asyncio.create_task(func(chart, *parsed))
            else:
                func(chart, *parsed)

        self.win.handlers[handler_id] = lambda *a: _wrapper(self, *a)
        self.run_script(f"""
            if (typeof {self.id}._dblClickHandler !== 'undefined') {{
                {self.id}.chart.unsubscribeDblClick({self.id}._dblClickHandler);
            }}
            {self.id}._dblClickHandler = (param) => {{
                if (!param.point) return;
                const time = {self.id}.chart.timeScale().coordinateToTime(param.point.x);
                const price = {self.id}.series.coordinateToPrice(param.point.y);
                window.callbackFunction(`{handler_id}_~_${{time}};;;${{price}}`);
            }};
            {self.id}.chart.subscribeDblClick({self.id}._dblClickHandler);
        null""")

    def unsubscribe_dbl_click(self):
        """Unsubscribes from double-click events."""
        salt = self.id.replace('window.', '')
        self.win.handlers.pop(f'dbl_click_{salt}', None)
        self.run_script(f"""
            if (typeof {self.id}._dblClickHandler !== 'undefined') {{
                {self.id}.chart.unsubscribeDblClick({self.id}._dblClickHandler);
                delete {self.id}._dblClickHandler;
            }}
        null""")

    def set_crosshair_position(self, price: float, time: TIME, series: "SeriesCommon"):
        """
        Programmatically sets the crosshair position.
        :param price: The price level.
        :param time: The time value (will be converted to unix seconds).
        :param series: The series the crosshair should snap to.
        """
        ts = int(pd.Timestamp(time).value // 10**9) if not isinstance(time, (int, float)) else int(time)
        self.run_script(
            f"{self.id}.chart.setCrosshairPosition({float(price)}, {ts}, {series.id}.series)"
        )

    def clear_crosshair_position(self):
        """Clears the crosshair position."""
        self.run_script(f"{self.id}.chart.clearCrosshairPosition()")

    def pane_size(self, pane_index: int = 0) -> dict:
        """
        Returns the ``{width, height}`` of the pane at *pane_index* (blocking).
        """
        result = self.win.run_script_and_get(
            f"JSON.stringify({self.id}.chart.paneSize({int(pane_index)}))"
        )
        return json.loads(result) if isinstance(result, str) else {}
