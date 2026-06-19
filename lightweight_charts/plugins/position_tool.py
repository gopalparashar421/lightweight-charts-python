from typing import TYPE_CHECKING

from ..util import NUM, TIME, Pane

if TYPE_CHECKING:
    from ..abstract import SeriesCommon


def _js_num(v) -> str:
    """Return ``'null'`` for ``None``, otherwise the numeric literal string."""
    return "null" if v is None else str(v)


def _js_str(v: str | None) -> str:
    """Return ``'null'`` for ``None``, otherwise a JS single-quoted string."""
    return "null" if v is None else f"'{v}'"


class PositionTool(Pane):
    """
    Risk/reward overlay that visualises an open trade position on the chart.

    The overlay consists of:

    * A **stop zone** (red rectangle) between the entry price and the
      stop-loss price.
    * A **target zone** (green rectangle) between the entry price and the
      take-profit price.

    The right edge of the overlay normally auto-tracks the latest bar on the
    attached series (always at least 15 bars wide from the entry).  Pass an
    explicit *end_time* to pin it.

    Price-ordering constraints
    --------------------------
    Long  position: ``target > entry > stop``
    Short position: ``stop   > entry > target``

    :param series:           The series (candlestick, line, …) to attach to.
    :param entry:            Entry price.
    :param stop:             Stop-loss price.
    :param target:           Take-profit price.
    :param entry_time:       Timestamp of the entry bar (left edge).
    :param end_time:         Optional right-edge timestamp.  ``None`` = auto.
    :param stop_color:       Fill colour of the risk zone rectangle.
    :param target_color:     Fill colour of the reward zone rectangle.
    :param quantity:         Number of units/contracts.  When provided, the
                             hover overlay shows monetary win/lose amounts
                             (e.g. ``+$125.00``).  Must be > 0.
    """

    def __init__(
        self,
        series: "SeriesCommon",
        entry: NUM,
        stop: NUM,
        target: NUM,
        entry_time: TIME,
        end_time: TIME | None = None,
        stop_color: str = "rgba(239, 83, 80, 0.25)",
        target_color: str = "rgba(38, 166, 154, 0.25)",
        quantity: NUM | None = None,
    ):
        super().__init__(series._chart.win)
        self._series = series

        self._validate(entry, stop, target, quantity=quantity)

        chart = series._chart
        entry_ts = chart._format_time(entry_time)
        end_ts = chart._format_time(end_time) if end_time is not None else "null"

        self.run_script(f"""
            {self.id} = new Lib.PositionTool({{
                entry:           {entry},
                stop:            {stop},
                target:          {target},
                entryTime:       {entry_ts},
                endTime:         {end_ts},
                stopColor:       '{stop_color}',
                targetColor:     '{target_color}',
                quantity:        {_js_num(quantity)},
            }});
            {series.id}.series.attachPrimitive({self.id});
        null""")

    # ── Public API ────────────────────────────────────────────────────────────

    def update(
        self,
        entry: NUM | None = None,
        stop: NUM | None = None,
        target: NUM | None = None,
        end_time: TIME | None = None,
        quantity: NUM | None = None,
    ) -> None:
        """
        Update one or more position parameters.

        Only the keyword arguments that are explicitly provided are changed;
        all others retain their current values.  Pass ``end_time`` to pin the
        right edge; omit it to leave the current auto-track / pinned state
        unchanged.

        :param entry:           New entry price.
        :param stop:            New stop-loss price.
        :param target:          New take-profit price.
        :param end_time:        New right-edge timestamp (``None`` skips update).
        :param quantity:        New position size (must be > 0 if provided).
        """
        if quantity is not None:
            self._validate(0, -1, 1, quantity=quantity)  # validate quantity only
        # Build a JS object literal from only the supplied arguments
        parts: list[str] = []
        if entry is not None:
            parts.append(f"entry: {entry}")
        if stop is not None:
            parts.append(f"stop: {stop}")
        if target is not None:
            parts.append(f"target: {target}")
        if end_time is not None:
            ts = self._series._chart._format_time(end_time)
            parts.append(f"endTime: {ts}")
        if quantity is not None:
            parts.append(f"quantity: {quantity}")

        if parts:
            self.run_script(f"{self.id}.applyOptions({{{', '.join(parts)}}})")

    def delete(self) -> None:
        """Detach and permanently remove the position overlay from the chart."""
        self.run_script(f"{self._series.id}.series.detachPrimitive({self.id})")

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _validate(entry: NUM, stop: NUM, target: NUM, quantity: NUM | None = None) -> None:
        if quantity is not None and quantity <= 0:
            raise ValueError(f"PositionTool: quantity must be greater than 0 (got {quantity}).")
        if stop == entry:
            raise ValueError("PositionTool: stop price must differ from entry price.")
        if target == entry:
            raise ValueError("PositionTool: target price must differ from entry price.")

        is_long = target > entry
        is_short = target < entry

        if is_long and not (entry > stop):
            raise ValueError(
                "PositionTool: long position requires target > entry > stop "
                f"(got entry={entry}, stop={stop}, target={target})."
            )
        if is_short and not (stop > entry):
            raise ValueError(
                "PositionTool: short position requires stop > entry > target "
                f"(got entry={entry}, stop={stop}, target={target})."
            )
