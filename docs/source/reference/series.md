# Series

## `SeriesCommon`

`SeriesCommon` is the base class for all series types. The methods below are
available on every series object (`Line`, `Area`, `Histogram`, and `Candlestick`).

````{py:class} SeriesCommon

___

```{py:method} set(df: pd.DataFrame, format_cols: bool)

Sets the series data from a `DataFrame`.

Columns are matched case-insensitively. For `Line`/`Area`/`Histogram`, the
value column should be named after the series `name` given at creation time,
or `value` when no name was set. For candlestick data: `time | open | high | low | close | volume`.

If `format_cols` is `True` (default), datetime columns are converted to Unix
seconds automatically.

```
___

```{py:method} update(series: pd.Series, historicalUpdate: bool)

Updates the series with a single new data point.

If the timestamp of the new point matches the last bar, the last bar is
overwritten. Otherwise, a new bar is appended.

When `historicalUpdate` is `True`, the chart viewport is not automatically
scrolled to the new data.

```
___

```{py:method} marker(time, position, shape, color, text) -> str

Creates a single marker on the series.

* `time` — bar timestamp (`datetime`, `pd.Timestamp`, or str). Defaults to the last bar.
* `position` — `'above'`, `'below'`, or `'inside'`.
* `shape` — `'arrow_up'`, `'arrow_down'`, `'circle'`, or `'square'`.
* `color` — CSS colour string.
* `text` — label text.

Returns a marker ID that can be passed to `remove_marker()`.

```
___

```{py:method} marker_list(markers: list) -> list

Creates multiple markers in a single call. Each element is a dict with the
same keys as `marker()`: `time`, `position`, `shape`, `color`, `text`.

Returns a list of marker IDs.

```
___

```{py:method} remove_marker(marker_id: str)

Removes the marker with the given ID.

```
___

```{py:method} clear_markers()

Removes all markers from the series.

```
___

```{py:method} horizontal_line(price, color, width, style, text, axis_label_visible, func) -> HorizontalLine

Creates a horizontal line at `price`.

```
___

```{py:method} trend_line(start_time, start_value, end_time, end_value, ...) -> TwoPointDrawing

Creates a trend line between two price/time coordinates.

```
___

```{py:method} box(start_time, start_value, end_time, end_value, ...) -> TwoPointDrawing

Creates a rectangular box drawing.

```
___

```{py:method} ray_line(start_time, value, ...) -> RayLine

Creates a ray line extending from a starting point.

```
___

```{py:method} vertical_line(time, ...) -> VerticalLine

Creates a vertical line at `time`.

```
___

```{py:method} vertical_span(start_time, end_time, color, round)

Creates a vertical span (shaded region) across the chart.

Can accept a single time, a `(start, end)` pair, or a list of times.

```
___

```{py:method} price_line(label_visible, line_visible, title)

Configures the last-price line and label visibility.

```
___

```{py:method} precision(precision: int)

Sets the decimal precision and minimum price movement for the series.

```
___

```{py:method} hide_data()

Hides the series data from view without deleting it.

```
___

```{py:method} show_data()

Shows a previously hidden series.

```
___

```{py:method} legend(visible, lines, color, font_size, font_family, text, pane_index)

Configures the legend for the pane this series lives on.

```
___

```{py:method} attach_primitive(js_constructor_call: str) -> AttachedPrimitive

Attaches a JavaScript primitive (custom drawing) to this series.
The expression must construct an object implementing LWC's `ISeriesPrimitive`.

Returns an `AttachedPrimitive` with a `.detach()` method.

Example:

```python
js = """
{
    draw(target) {
        // custom WebGL/Canvas2D drawing
    }
}
"""
primitive = series.attach_primitive(f"({js})")
# later:
primitive.detach()
```

___

```{py:method} options() -> dict

Returns the current series options as a dict (blocking call).

```
___

```{py:method} get_data() -> list

Returns all series data as a list of dicts (blocking call).

```
___

```{py:method} move_to_pane(pane_index: int)

Moves this series to the pane at the given index.

```
___

```{py:method} get_pane() -> Pane

Returns the `Pane` object for the pane this series lives on (blocking call).

```
___

```{py:method} subscribe_data_changed(func: callable)

Subscribes to data-change events on this series. The callable receives the
series as its first argument. Async functions are supported.

```
___

```{py:method} unsubscribe_data_changed()

Unsubscribes from data-change events.

```

````

---

## `Line`

````{py:class} Line(name: str, color: COLOR, style: LINE_STYLE, type: LINE_TYPE, width: int, price_line: bool, price_label: bool, price_scale_id: str, last_price_animation: str, pane_index: int)
:no-index:

A `LineSeries` in Lightweight Charts. Created via `chart.create_line()`.

Inherits all `SeriesCommon` methods.

`last_price_animation` accepts `'disabled'`, `'continuous'`, or `'one_shot'`.

___

```{py:method} delete():no-index:
Irreversibly deletes the line series.

```

````

---

## `Area`

````{py:class} Area(name: str, top_color: COLOR, bottom_color: COLOR, line_color: COLOR, line_width: int, price_line: bool, price_label: bool, pane_index: int)

An `AreaSeries` in Lightweight Charts with gradient fill. Created via `chart.create_area()`.

Inherits all `SeriesCommon` methods. Additionally, `set()` and `update()` accept
per-point colour columns/keys: `line_color`, `top_color`, `bottom_color` (camelCase variants also accepted).

___

```{py:method} delete()

Irreversibly deletes the area series.

```

````

---

## `Histogram`

````{py:class} Histogram(name: str, color: COLOR, price_line: bool, price_label: bool, scale_margin_top: float, scale_margin_bottom: float, pane_index: int, price_scale_id: str)
:no-index:

A `HistogramSeries` in Lightweight Charts. Created via `chart.create_histogram()`.

Inherits all `SeriesCommon` methods.

___

```{py:method} delete():no-index:
Irreversibly deletes the histogram series.

```
___

```{py:method} scale(scale_margin_top: float, scale_margin_bottom: float)
:no-index:

Configures the histogram's price scale margins.

```

````

---

## `AttachedPrimitive`

````{py:class} AttachedPrimitive(series, js_constructor_call: str)

Wraps a JavaScript series primitive attached via `series.attach_primitive()`.

___

```{py:method} detach()

Detaches the primitive from the series.

```
___

```{py:method} update_options(options: dict)

Calls `applyOptions()` on the primitive, updating its configuration.

```

````

---

## `UpDownMarkers`

````{py:class} UpDownMarkers(chart, series, up_color: COLOR, down_color: COLOR)

Attaches up/down marker primitives to a series using Lightweight Charts v5's
`createUpDownMarkers` API. Created automatically for candlestick-type series
or attached to any series manually.

___

```{py:method} detach()

Detaches the up/down markers from the series.

```

````
