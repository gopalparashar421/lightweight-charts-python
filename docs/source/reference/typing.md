:orphan:

# `Typing`

These classes serve as placeholders for type requirements.


```{py:class} NUM(Literal[float, int])
```

```{py:class} FLOAT(Literal['left', 'right', 'top', 'bottom'])
```

```{py:class} TIME(Union[datetime, pd.Timestamp, str])
```

```{py:class} COLOR(str)
Throughout the library, colors should be given as either rgb (`rgb(100, 100, 100)`), rgba(`rgba(100, 100, 100, 0.7)`), hex(`#32a852`) or a html literal(`blue`, `red` etc).
```

```{py:class} LINE_STYLE(Literal['solid', 'dotted', 'dashed', 'large_dashed', 'sparse_dotted'])
```

```{py:class} LINE_TYPE(Literal['simple', 'with_steps', 'curved'])
```

```{py:class} MARKER_POSITION(Literal['above', 'below', 'inside'])
```

```{py:class} MARKER_SHAPE(Literal['arrow_up', 'arrow_down', 'circle', 'square'])
```

```{py:class} CROSSHAIR_MODE(Literal['normal', 'magnet'])
```

```{py:class} PRICE_SCALE_MODE(Literal['normal', 'logarithmic', 'percentage', 'index100'])
```

```{py:class} ALIGN(Literal['left', 'right'])
```

```{py:class} BOX_TEXT_POSITION(Literal['center', 'left', 'right', 'top', 'bottom'])
Used by `box()` to select which edge or corner anchors the label.
```

```{py:class} BOX_TEXT_PLACEMENT(Literal['inside', 'outside'])
Used by `box()` to draw the label inside the rectangle or just outside it on the chosen edge. Defaults to `'outside'`.
```

```{py:class} LINE_TEXT_POSITION(Literal['above', 'below'])
Used by `horizontal_line()` and `ray_line()`.
```

```{py:class} TREND_LINE_TEXT_POSITION(Literal['center', 'start', 'end'])
Used by `trend_line()`.
```

```{py:class} VERTICAL_TEXT_H_ALIGN(Literal['left', 'center', 'right'])
Used by `vertical_line()`.
```

```{py:class} VERTICAL_TEXT_V_ALIGN(Literal['top', 'center', 'bottom'])
Used by `vertical_line()`.
```
