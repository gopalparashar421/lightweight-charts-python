# `Pane`

````{py:class} Pane(chart, pane_index: int)

`Pane` is a Python wrapper around LWC's `IPaneApi`. It represents a single chart pane and provides methods for resizing, reordering, and introspecting that pane.

Instances are created by calling `chart.panes()` — do not instantiate directly.

> **Stale instances:** Pane objects become stale after structural pane changes such as `remove_pane()` or `swap_panes()`. Re-call `chart.panes()` after such operations.

___


```{py:method} get_height() -> int

Returns the pane height in pixels (blocking call).

```
___

```{py:method} set_height(height: int)

Sets the pane height in pixels.

```
___

```{py:method} get_stretch_factor() -> float

Returns the relative height factor of this pane (blocking call).

```
___

```{py:method} set_stretch_factor(factor: float)

Sets the relative height factor for this pane.

```
___

```{py:method} move_to(pane_index: int)

Reorders this pane to the given index.

```
___

```{py:method} pane_index() -> int

Returns the current pane index (uses cached value).

```
___

```{py:method} get_series() -> list

Returns the list of `SeriesCommon` objects on this pane that are tracked in the parent chart's series registry.

```
___

```{py:method} attach_primitive(js_constructor_call: str) -> AttachedPanePrimitive

Attaches a JavaScript primitive at the pane level. The primitive must implement LWC's `IPanePrimitive` interface.

Returns an `AttachedPanePrimitive` instance with a `.detach()` method.

```
___

```{py:method} detach_primitive(primitive: AttachedPanePrimitive)

Detaches a previously attached pane primitive.

```
___

```{py:method} set_preserve_empty_pane(preserve: bool)

Sets whether this pane is preserved when all its series are removed.

```
___

```{py:method} preserve_empty_pane() -> bool

Returns whether the empty-pane preservation flag is set (blocking call).

```

````

## Pane management on `AbstractChart`

The following methods on `AbstractChart` manage panes:

```{py:method} add_pane(height: int)

Adds a new pane to the chart. Optionally specify `height` in pixels.

```
___

```{py:method} get_pane_count() -> int

Returns the current number of panes in the chart (blocking call).

```
___

```{py:method} panes() -> list

Returns a list of `Pane` objects, one per pane. The list is rebuilt on each call.

```
___

```{py:method} resize_pane(pane_index: int, height: int)

Resizes the pane at `pane_index` to `height` pixels.

```
___

```{py:method} remove_pane(pane_index: int)

Removes the pane at `pane_index`.

```
___

```{py:method} swap_panes(first: int, second: int)

Swaps the panes at indices `first` and `second`.

```
