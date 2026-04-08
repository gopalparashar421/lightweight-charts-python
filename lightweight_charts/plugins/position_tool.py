from typing import TYPE_CHECKING, Optional

from ..util import Pane, NUM, TIME

if TYPE_CHECKING:
    from ..abstract import SeriesCommon


def _js_num(v) -> str:
    """Return ``'null'`` for ``None``, otherwise the numeric literal string."""
    return 'null' if v is None else str(v)


def _js_str(v: Optional[str]) -> str:
    """Return ``'null'`` for ``None``, otherwise a JS single-quoted string."""
    return 'null' if v is None else f"'{v}'"


class PositionTool(Pane):
    """
    Risk/reward overlay that visualises an open trade position on the chart.

    The overlay consists of:

    * A **stop zone** (red rectangle) between the entry price and the
      stop-loss price.
    * A **target zone** (green rectangle) between the entry price and the
      take-profit price.
    * A dashed **entry line** at the entry price.
    * **Metric labels** inside each zone showing risk/reward in points, %,
      and optionally currency amounts when *account_balance* and
      *risk_percent* are provided.

    The right edge of the overlay normally auto-tracks the latest bar on the
    attached series (always at least 5 bars wide from the entry).  Pass an
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
    :param entry_line_color: Colour of the dashed entry-price line.
    :param text_color:       Colour of all metric label text.
    :param account_balance:  Account balance used to compute currency labels.
    :param risk_percent:     Percentage of account risked (e.g. ``1`` = 1 %).
    """

    def __init__(
        self,
        series: "SeriesCommon",
        entry: NUM,
        stop: NUM,
        target: NUM,
        entry_time: TIME,
        end_time: Optional[TIME] = None,
        stop_color: str = 'rgba(239, 83, 80, 0.25)',
        target_color: str = 'rgba(38, 166, 154, 0.25)',
        entry_line_color: str = '#FFD700',
        text_color: str = 'rgba(255, 255, 255, 0.85)',
        account_balance: Optional[NUM] = None,
        risk_percent: Optional[NUM] = None,
    ):
        super().__init__(series._chart.win)
        self._series = series

        self._validate(entry, stop, target)

        chart = series._chart
        entry_ts = chart._single_datetime_format(entry_time)
        end_ts   = chart._single_datetime_format(end_time) if end_time is not None else 'null'

        self.run_script(f'''
            {self.id} = new Lib.PositionTool({{
                entry:           {entry},
                stop:            {stop},
                target:          {target},
                entryTime:       {entry_ts},
                endTime:         {end_ts},
                stopColor:       '{stop_color}',
                targetColor:     '{target_color}',
                entryLineColor:  '{entry_line_color}',
                textColor:       '{text_color}',
                accountBalance:  {_js_num(account_balance)},
                riskPercent:     {_js_num(risk_percent)},
            }});
            {series.id}.series.attachPrimitive({self.id});
        null''')

    # ── Public API ────────────────────────────────────────────────────────────

    def update(
        self,
        entry: Optional[NUM] = None,
        stop: Optional[NUM] = None,
        target: Optional[NUM] = None,
        end_time: Optional[TIME] = None,
        account_balance: Optional[NUM] = None,
        risk_percent: Optional[NUM] = None,
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
        :param account_balance: New account balance.
        :param risk_percent:    New risk percentage.
        """
        # Build a JS object literal from only the supplied arguments
        parts: list[str] = []
        if entry is not None:
            parts.append(f'entry: {entry}')
        if stop is not None:
            parts.append(f'stop: {stop}')
        if target is not None:
            parts.append(f'target: {target}')
        if end_time is not None:
            ts = self._series._chart._single_datetime_format(end_time)
            parts.append(f'endTime: {ts}')
        if account_balance is not None:
            parts.append(f'accountBalance: {account_balance}')
        if risk_percent is not None:
            parts.append(f'riskPercent: {risk_percent}')

        if parts:
            self.run_script(f'{self.id}.applyOptions({{{", ".join(parts)}}})')

    def delete(self) -> None:
        """Detach and permanently remove the position overlay from the chart."""
        self.run_script(f'{self._series.id}.series.detachPrimitive({self.id})')

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _validate(entry: NUM, stop: NUM, target: NUM) -> None:
        if stop == entry:
            raise ValueError("PositionTool: stop price must differ from entry price.")
        if target == entry:
            raise ValueError("PositionTool: target price must differ from entry price.")

        is_long  = target > entry
        is_short = target < entry

        if is_long  and not (entry > stop):
            raise ValueError(
                "PositionTool: long position requires target > entry > stop "
                f"(got entry={entry}, stop={stop}, target={target})."
            )
        if is_short and not (stop > entry):
            raise ValueError(
                "PositionTool: short position requires stop > entry > target "
                f"(got entry={entry}, stop={stop}, target={target})."
            )
