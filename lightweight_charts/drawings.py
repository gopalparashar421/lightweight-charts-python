import inspect

import pandas as pd

from .util import (
    BOX_TEXT_PLACEMENT,
    BOX_TEXT_POSITION,
    LINE_STYLE,
    LINE_TEXT_POSITION,
    NUM,
    TIME,
    TREND_LINE_TEXT_POSITION,
    VERTICAL_TEXT_H_ALIGN,
    VERTICAL_TEXT_V_ALIGN,
    Pane,
    as_enum,
    jbool,
)


def make_js_point(chart, time, price, round: bool = False):
    formatted_time = chart._format_time(time, round=round)
    return f"""{{
        "time": {formatted_time},
        "logical": {chart.id}.chart.timeScale()
                    .coordinateToLogical(
                        {chart.id}.chart.timeScale()
                        .timeToCoordinate({formatted_time})
                    ),
        "price": {price}
    }}"""


def _text_color_js(text_color, line_color):
    return text_color if text_color is not None else line_color


class Drawing(Pane):
    def __init__(self, chart, func=None, round: bool = False):
        super().__init__(chart.win)
        self.chart = chart
        self._round = round

    def update(self, *points):
        formatted_points = []
        for i in range(0, len(points), 2):
            formatted_points.append(
                make_js_point(self.chart, points[i], points[i + 1], round=self._round)
            )
        self.run_script(f"{self.id}.updatePoints({', '.join(formatted_points)})")

    def delete(self):
        """
        Irreversibly deletes the drawing.
        """
        self.run_script(f"{self.id}.detach()")

    def options(self, color="#1E80F0", style="solid", width=4):
        self.run_script(f"""{self.id}.applyOptions({{
            lineColor: '{color}',
            lineStyle: {as_enum(style, LINE_STYLE)},
            width: {width},
        }})""")


class TwoPointDrawing(Drawing):
    def __init__(
        self,
        drawing_type,
        chart,
        start_time: TIME,
        start_value: NUM,
        end_time: TIME,
        end_value: NUM,
        round: bool,
        options: dict,
        func=None,
    ):
        super().__init__(chart, func, round=round)

        options_string = "\n".join(f"{key}: {val}," for key, val in options.items())

        self.run_script(f"""
        {self.id} = new Lib.{drawing_type}(
            {make_js_point(self.chart, start_time, start_value, round=round)},
            {make_js_point(self.chart, end_time, end_value, round=round)},
            {{
                {options_string}
            }}
        )
        {chart.id}.series.attachPrimitive({self.id})
        """)


class HorizontalLine(Drawing):
    def __init__(
        self,
        chart,
        price,
        color,
        width,
        style,
        text,
        text_position,
        axis_label_visible,
        text_color,
        func,
    ):
        super().__init__(chart, func)
        self.price = price
        self.run_script(f"""

        {self.id} = new Lib.HorizontalLine(
            {{price: {price}}},
            {{
                lineColor: '{color}',
                lineStyle: {as_enum(style, LINE_STYLE)},
                width: {width},
                text: `{text}`,
                textColor: '{_text_color_js(text_color, color)}',
                textPosition: '{text_position}',
                axisLabelVisible: {jbool(axis_label_visible)},
            }},
            callbackName={f"'{self.id}'" if func else "null"}
        )
        {chart.id}.series.attachPrimitive({self.id})
        """)
        if not func:
            return

        def wrapper(p):
            self.price = float(p)
            func(chart, self)

        async def wrapper_async(p):
            self.price = float(p)
            await func(chart, self)

        self.win.handlers[self.id] = wrapper_async if inspect.iscoroutinefunction(func) else wrapper
        self.run_script(f"{chart.id}.toolBox?.addNewDrawing({self.id})")

    def update(self, price: float):
        """
        Moves the horizontal line to the given price.
        """
        self.run_script(f"{self.id}.updatePoints({{price: {price}}})")
        self.price = price

    def options(
        self,
        color="#1E80F0",
        style="solid",
        width=4,
        text="",
        text_position: LINE_TEXT_POSITION = "above",
        axis_label_visible: bool = True,
        text_color: str | None = None,
    ):
        super().options(color, style, width)
        self.run_script(f"""{self.id}.applyOptions({{
            text: `{text}`,
            textColor: '{_text_color_js(text_color, color)}',
            textPosition: '{text_position}',
            axisLabelVisible: {jbool(axis_label_visible)},
        }})""")


class VerticalLine(Drawing):
    def __init__(
        self,
        chart,
        time,
        color,
        width,
        style,
        text,
        text_h_align,
        text_v_align,
        text_color,
        func=None,
    ):
        super().__init__(chart, func)
        self.time = time
        self.run_script(f"""

        {self.id} = new Lib.VerticalLine(
            {{time: {self.chart._format_time(time)}}},
            {{
                lineColor: '{color}',
                lineStyle: {as_enum(style, LINE_STYLE)},
                width: {width},
                text: `{text}`,
                textColor: '{_text_color_js(text_color, color)}',
                textHAlign: '{text_h_align}',
                textVAlign: '{text_v_align}',
            }},
            callbackName={f"'{self.id}'" if func else "null"}
        )
        {chart.id}.series.attachPrimitive({self.id})
        """)

    def update(self, time: TIME):
        formatted_time = self.chart._format_time(time)
        self.run_script(f"{self.id}.updatePoints({{time: {formatted_time}}})")

    def options(
        self,
        color="#1E80F0",
        style="solid",
        width=4,
        text="",
        text_h_align: VERTICAL_TEXT_H_ALIGN = "center",
        text_v_align: VERTICAL_TEXT_V_ALIGN = "center",
        text_color: str | None = None,
    ):
        super().options(color, style, width)
        self.run_script(f"""{self.id}.applyOptions({{
            text: `{text}`,
            textColor: '{_text_color_js(text_color, color)}',
            textHAlign: '{text_h_align}',
            textVAlign: '{text_v_align}',
        }})""")


class RayLine(Drawing):
    def __init__(
        self,
        chart,
        start_time: TIME,
        value: NUM,
        round: bool = False,
        color: str = "#1E80F0",
        width: int = 2,
        style: LINE_STYLE = "solid",
        text: str = "",
        text_position: LINE_TEXT_POSITION = "above",
        axis_label_visible: bool = True,
        text_color: str | None = None,
        func=None,
    ):
        super().__init__(chart, func, round=round)
        formatted_time = chart._format_time(start_time, round=round)
        self.run_script(f"""
        {self.id} = new Lib.RayLine(
            {{time: {formatted_time}, price: {value}}},
            {{
                lineColor: '{color}',
                lineStyle: {as_enum(style, LINE_STYLE)},
                width: {width},
                text: `{text}`,
                textColor: '{_text_color_js(text_color, color)}',
                textPosition: '{text_position}',
                axisLabelVisible: {jbool(axis_label_visible)},
            }},
            callbackName={f"'{self.id}'" if func else "null"}
        )
        {chart.id}.series.attachPrimitive({self.id})
        """)

    def options(
        self,
        color="#1E80F0",
        style="solid",
        width=4,
        text="",
        text_position: LINE_TEXT_POSITION = "above",
        axis_label_visible: bool = True,
        text_color: str | None = None,
    ):
        super().options(color, style, width)
        self.run_script(f"""{self.id}.applyOptions({{
            text: `{text}`,
            textColor: '{_text_color_js(text_color, color)}',
            textPosition: '{text_position}',
            axisLabelVisible: {jbool(axis_label_visible)},
        }})""")


class Box(TwoPointDrawing):
    def __init__(
        self,
        chart,
        start_time: TIME,
        start_value: NUM,
        end_time: TIME,
        end_value: NUM,
        round: bool,
        line_color: str,
        fill_color: str,
        width: int,
        style: LINE_STYLE,
        text: str = "",
        text_position: BOX_TEXT_POSITION = "center",
        text_placement: BOX_TEXT_PLACEMENT = "outside",
        text_color: str | None = None,
        func=None,
    ):
        super().__init__(
            "Box",
            chart,
            start_time,
            start_value,
            end_time,
            end_value,
            round,
            {
                "lineColor": f'"{line_color}"',
                "fillColor": f'"{fill_color}"',
                "width": width,
                "lineStyle": as_enum(style, LINE_STYLE),
                "text": f"`{text}`",
                "textColor": f'"{_text_color_js(text_color, line_color)}"',
                "textPosition": f'"{text_position}"',
                "textPlacement": f'"{text_placement}"',
            },
            func,
        )

    def options(
        self,
        color="#1E80F0",
        style="solid",
        width=4,
        fill_color: str | None = None,
        text: str = "",
        text_position: BOX_TEXT_POSITION = "center",
        text_placement: BOX_TEXT_PLACEMENT = "outside",
        text_color: str | None = None,
    ):
        super().options(color, style, width)
        opts = [
            f"text: `{text}`",
            f"textColor: '{_text_color_js(text_color, color)}'",
            f"textPosition: '{text_position}'",
            f"textPlacement: '{text_placement}'",
        ]
        if fill_color is not None:
            opts.append(f'fillColor: "{fill_color}"')
        self.run_script(f"{self.id}.applyOptions({{{', '.join(opts)}}})")


class TrendLine(TwoPointDrawing):
    def __init__(
        self,
        chart,
        start_time: TIME,
        start_value: NUM,
        end_time: TIME,
        end_value: NUM,
        round: bool,
        line_color: str,
        width: int,
        style: LINE_STYLE,
        text: str = "",
        text_position: TREND_LINE_TEXT_POSITION = "center",
        text_color: str | None = None,
        func=None,
    ):
        super().__init__(
            "TrendLine",
            chart,
            start_time,
            start_value,
            end_time,
            end_value,
            round,
            {
                "lineColor": f'"{line_color}"',
                "width": width,
                "lineStyle": as_enum(style, LINE_STYLE),
                "text": f"`{text}`",
                "textColor": f'"{_text_color_js(text_color, line_color)}"',
                "textPosition": f'"{text_position}"',
            },
            func,
        )

    def options(
        self,
        color="#1E80F0",
        style="solid",
        width=4,
        text: str = "",
        text_position: TREND_LINE_TEXT_POSITION = "center",
        text_color: str | None = None,
    ):
        super().options(color, style, width)
        self.run_script(f"""{self.id}.applyOptions({{
            text: `{text}`,
            textColor: '{_text_color_js(text_color, color)}',
            textPosition: '{text_position}',
        }})""")


# TODO reimplement/fix
class VerticalSpan(Pane):
    def __init__(
        self,
        series,
        start_time: TIME | tuple | list,
        end_time: TIME | None = None,
        color: str = "rgba(252, 219, 3, 0.2)",
    ):
        self._chart = series._chart
        super().__init__(self._chart.win)
        start_time, end_time = pd.to_datetime(start_time), pd.to_datetime(end_time)
        self.run_script(f"""
        {self.id} = {self._chart.id}.chart.addHistogramSeries({{
                color: '{color}',
                priceFormat: {{type: 'volume'}},
                priceScaleId: 'vertical_line',
                lastValueVisible: false,
                priceLineVisible: false,
        }})
        {self.id}.priceScale('').applyOptions({{
            scaleMargins: {{top: 0, bottom: 0}}
        }})
        """)
        if end_time is None:
            if isinstance(start_time, pd.DatetimeIndex):
                data = [{"time": time.timestamp(), "value": 1} for time in start_time]
            else:
                data = [{"time": start_time.timestamp(), "value": 1}]
            self.run_script(f"{self.id}.setData({data})")
        else:
            self.run_script(f"""
            {self.id}.setData(calculateTrendLine(
            {start_time.timestamp()}, 1, {end_time.timestamp()}, 1, {series.id}))
            """)

    def delete(self):
        """
        Irreversibly deletes the vertical span.
        """
        self.run_script(f"{self._chart.id}.chart.removeSeries({self.id})")
