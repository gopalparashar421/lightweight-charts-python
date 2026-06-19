# `HorizontalLine`


````{py:class} HorizontalLine(price: NUM, color: COLOR, width: int, style: LINE_STYLE, text: str, text_position: LINE_TEXT_POSITION, axis_label_visible: bool, text_color: COLOR, func: callable= None)

The `HorizontalLine` object represents a `PriceLine` in Lightweight Charts.

`text` / `text_position`
: Optional on-chart label (`"above"` or `"below"`).

`axis_label_visible`
: When `False`, hides the numeric price label on the right-hand axis.

Its instance should be accessed from the `horizontal_line` method.



```{py:method} update(price: NUM)

Updates the price of the horizontal line.
```


```{py:method} options(color, style, width, text, text_position, axis_label_visible, text_color)

Updates line style and label options at runtime.
```


```{py:method} label(text: str)

Updates the label of the horizontal line.
```


```{py:method} delete()

Irreversibly deletes the horizontal line.
```
````
