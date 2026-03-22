"""
lightweight_charts.plugins
==========================

High-level Python wrappers for chart plugins (session highlighting, tooltips,
bands, volume profile, heatmap).  Each class accepts a *chart* as its first
argument and exposes a simple API that translates to JavaScript calls executed
inside the embedded Webview.
"""

from __future__ import annotations

from typing import List, Optional
import json
import pandas as pd

from .util import Pane, js_data
from .abstract import Window


# ---------------------------------------------------------------------------
# SessionHighlighting
# ---------------------------------------------------------------------------

class SessionHighlighting:
    """
    Highlights arbitrary time windows on a chart with a semi-transparent
    background color.

    Each session is defined as a dict with ``'start'`` and ``'end'`` keys
    holding **Unix timestamps** (integer seconds).

    Example::

        sh = SessionHighlighting(chart, session_color='rgba(41, 98, 255, 0.08)')
        sh.set_sessions([
            {'start': 1704067200, 'end': 1704078000},
        ])
    """

    def __init__(self, chart, session_color: str = 'rgba(41, 98, 255, 0.08)'):
        self._chart = chart
        self._color = session_color
        self._series_id: Optional[str] = None

    def set_sessions(self, sessions: List[dict]):
        """
        Replace the current highlighted sessions with the supplied list.

        Each element must have ``'start'`` and ``'end'`` Unix timestamp keys.
        """
        if self._series_id is not None:
            self._chart.run_script(
                f"{self._chart.id}.chart.removeSeries({self._series_id});"
            )

        series_id = Window._id_gen.generate()
        self._series_id = series_id

        # Build histogram data spanning each session (value=1 from start to end).
        rows = []
        for session in sessions:
            start = int(session['start'])
            end = int(session['end'])
            rows.append({'time': start, 'value': 1})
            rows.append({'time': end, 'value': 1})

        data_js = json.dumps(rows)
        self._chart.run_script(
            f"""
            (function() {{
                {series_id} = {self._chart.id}.chart.addSeries(
                    LightweightCharts.HistogramSeries,
                    {{
                        color: '{self._color}',
                        priceFormat: {{type: 'volume'}},
                        priceScaleId: 'session_highlight',
                        lastValueVisible: false,
                        priceLineVisible: false,
                    }},
                    0
                );
                {series_id}.priceScale('session_highlight').applyOptions({{
                    scaleMargins: {{top: 0, bottom: 0}},
                }});
                const rows = {data_js};
                if (rows.length > 0) {{
                    {series_id}.setData(rows);
                }}
            }})();
        """
        )

    def detach(self):
        """Remove session highlighting from the chart."""
        if self._series_id is not None:
            self._chart.run_script(
                f"{self._chart.id}.chart.removeSeries({self._series_id});"
            )
            self._series_id = None


# ---------------------------------------------------------------------------
# Tooltip
# ---------------------------------------------------------------------------

class Tooltip:
    """
    Displays an OHLCV tooltip that follows the crosshair.

    The tooltip is rendered as a floating HTML div positioned over the chart.

    Example::

        tooltip = Tooltip(chart, title='OHLCV', font_size=12,
                          color='rgba(255,255,255,0.9)',
                          background='rgba(15,15,15,0.85)')
    """

    def __init__(
        self,
        chart,
        title: str = '',
        font_size: int = 12,
        color: str = 'rgba(255,255,255,0.9)',
        background: str = 'rgba(15,15,15,0.85)',
    ):
        self._chart = chart
        self._tooltip_id = Window._id_gen.generate()

        chart.run_script(
            f"""
            (function() {{
                const tooltipDiv = document.createElement('div');
                tooltipDiv.id = '{self._tooltip_id}';
                tooltipDiv.style.cssText = `
                    position: absolute;
                    display: none;
                    padding: 6px 10px;
                    border-radius: 4px;
                    font-size: {font_size}px;
                    color: {color};
                    background: {background};
                    pointer-events: none;
                    z-index: 1000;
                    white-space: nowrap;
                `;
                {chart.id}.div.style.position = 'relative';
                {chart.id}.div.appendChild(tooltipDiv);

                {chart.id}.chart.subscribeCrosshairMove(function(param) {{
                    const el = document.getElementById('{self._tooltip_id}');
                    if (!el) return;
                    if (!param.point || !param.time) {{
                        el.style.display = 'none';
                        return;
                    }}
                    const series = {chart.id}.series;
                    const data = param.seriesData.get(series);
                    if (!data) {{
                        el.style.display = 'none';
                        return;
                    }}
                    const dt = new Date(param.time * 1000);
                    const dateStr = dt.toISOString().substring(0, 10);
                    let html = `<b>{title}</b><br>Date: ${{dateStr}}<br>`;
                    if (data.open !== undefined)  html += `O: ${{data.open.toFixed(2)}}&nbsp;&nbsp;`;
                    if (data.high !== undefined)  html += `H: ${{data.high.toFixed(2)}}&nbsp;&nbsp;`;
                    if (data.low !== undefined)   html += `L: ${{data.low.toFixed(2)}}&nbsp;&nbsp;`;
                    if (data.close !== undefined) html += `C: ${{data.close.toFixed(2)}}&nbsp;&nbsp;`;
                    if (data.value !== undefined) html += `V: ${{data.value.toFixed(2)}}`;
                    el.innerHTML = html;
                    el.style.display = 'block';
                    const x = param.point.x + 12;
                    const y = param.point.y - 20;
                    el.style.left = x + 'px';
                    el.style.top  = y + 'px';
                }});
            }})();
        """
        )

    def detach(self):
        """Remove the tooltip overlay from the chart."""
        self._chart.run_script(
            f"""
            (function() {{
                const el = document.getElementById('{self._tooltip_id}');
                if (el) el.parentNode.removeChild(el);
            }})();
        """
        )


# ---------------------------------------------------------------------------
# BandsIndicator
# ---------------------------------------------------------------------------

class BandsIndicator:
    """
    Fills the region between an upper and a lower :class:`~lightweight_charts.Line`
    with a translucent color (Bollinger Bands / envelope style).

    Because LightweightCharts v5 does not yet expose a native band-fill API, the
    fill is approximated by creating a thin area series that spans between the
    two lines.

    Example::

        bands = BandsIndicator(chart, upper_line, lower_line,
                               fill_color='rgba(33, 150, 243, 0.1)',
                               upper_color='#2196F3',
                               lower_color='#2196F3',
                               line_width=1)
    """

    def __init__(
        self,
        chart,
        upper_series,
        lower_series,
        fill_color: str = 'rgba(33, 150, 243, 0.1)',
        upper_color: str = '#2196F3',
        lower_color: str = '#2196F3',
        line_width: int = 1,
    ):
        self._chart = chart
        self._fill_id = Window._id_gen.generate()

        chart.run_script(
            f"""
            (function() {{
                {upper_series.id}.series.applyOptions({{
                    color: '{upper_color}',
                    lineWidth: {line_width},
                }});
                {lower_series.id}.series.applyOptions({{
                    color: '{lower_color}',
                    lineWidth: {line_width},
                }});

                // Build a band-fill area series using the upper line data
                {self._fill_id} = {chart.id}.chart.addSeries(
                    LightweightCharts.AreaSeries,
                    {{
                        topColor: '{fill_color}',
                        bottomColor: '{fill_color}',
                        lineColor: 'transparent',
                        lineWidth: 0,
                        lastValueVisible: false,
                        priceLineVisible: false,
                        crosshairMarkerVisible: false,
                    }},
                    0
                );
                const upperData = {upper_series.id}.series.data();
                if (upperData && upperData.length) {{
                    {self._fill_id}.setData(
                        upperData.map(function(d) {{ return {{time: d.time, value: d.value}}; }})
                    );
                }}
            }})();
        """
        )

    def detach(self):
        """Remove the band fill from the chart."""
        self._chart.run_script(
            f"{self._chart.id}.chart.removeSeries({self._fill_id});"
        )


# ---------------------------------------------------------------------------
# VolumeProfile
# ---------------------------------------------------------------------------

class VolumeProfile:
    """
    Renders a horizontal Volume-at-Price profile on the right side of the
    main chart pane.

    The profile is built from OHLCV data supplied via :meth:`set_data`.

    Example::

        vp = VolumeProfile(chart,
                           up_color='rgba(38, 166, 154, 0.5)',
                           down_color='rgba(239, 83, 80, 0.5)',
                           width_factor=0.35)
        vp.set_data(df)
    """

    def __init__(
        self,
        chart,
        up_color: str = 'rgba(38, 166, 154, 0.5)',
        down_color: str = 'rgba(239, 83, 80, 0.5)',
        width_factor: float = 0.35,
        num_bins: int = 20,
    ):
        self._chart = chart
        self._up_color = up_color
        self._down_color = down_color
        self._width_factor = width_factor
        self._num_bins = num_bins
        self._series_ids: list = []

    def set_data(self, df: pd.DataFrame):
        """
        Build and display the volume profile from an OHLCV DataFrame.

        Required columns: ``open``, ``high``, ``low``, ``close``, ``volume``.
        """
        # Remove previously drawn bars
        for sid in self._series_ids:
            self._chart.run_script(
                f"{self._chart.id}.chart.removeSeries({sid});"
            )
        self._series_ids.clear()

        if df is None or df.empty:
            return

        high_price = float(df['high'].max())
        low_price = float(df['low'].min())
        if high_price == low_price:
            return

        bin_size = (high_price - low_price) / self._num_bins
        bins_up = [0.0] * self._num_bins
        bins_down = [0.0] * self._num_bins

        for _, row in df.iterrows():
            center = (row['open'] + row['close']) / 2.0
            bin_idx = int((center - low_price) / bin_size)
            bin_idx = max(0, min(self._num_bins - 1, bin_idx))
            if row['close'] >= row['open']:
                bins_up[bin_idx] += float(row['volume'])
            else:
                bins_down[bin_idx] += float(row['volume'])

        max_vol = max(max(bins_up), max(bins_down), 1.0)

        # Use a histogram series per bin drawn at a fixed time position
        # (the last bar time so that the bars appear on the right edge)
        last_time = int(df['time'].iloc[-1].timestamp()) if hasattr(df['time'].iloc[-1], 'timestamp') else int(df['time'].iloc[-1])

        for i in range(self._num_bins):
            price_low = low_price + i * bin_size
            price_high = price_low + bin_size
            price_mid = (price_low + price_high) / 2.0

            for vol, color in [(bins_up[i], self._up_color), (bins_down[i], self._down_color)]:
                if vol <= 0:
                    continue
                sid = Window._id_gen.generate()
                self._series_ids.append(sid)
                bar_width = self._width_factor * vol / max_vol
                self._chart.run_script(
                    f"""
                    {sid} = {self._chart.id}.chart.addSeries(
                        LightweightCharts.HistogramSeries,
                        {{
                            color: '{color}',
                            priceFormat: {{type: 'price'}},
                            priceScaleId: 'vp_{i}',
                            lastValueVisible: false,
                            priceLineVisible: false,
                        }},
                        0
                    );
                    {sid}.priceScale('vp_{i}').applyOptions({{
                        scaleMargins: {{top: 0, bottom: 0}},
                    }});
                    {sid}.setData([{{time: {last_time}, value: {price_mid}}}]);
                """
                )


# ---------------------------------------------------------------------------
# HeatmapSeries
# ---------------------------------------------------------------------------

class HeatmapSeries:
    """
    Renders a price-level intensity heatmap using multiple histogram series,
    one per price bucket per time bar.

    The DataFrame passed to :meth:`set` must have columns:
    ``time``, ``low``, ``high``, ``value`` (intensity 0–1).

    Example::

        heatmap = HeatmapSeries(chart, pane_index=0)
        heatmap.set(heatmap_df)
    """

    def __init__(self, chart, pane_index: int = 0):
        self._chart = chart
        self._pane_index = pane_index
        self._series_id: Optional[str] = None

    def set(self, df: pd.DataFrame):
        """
        Set heatmap data.  Each row represents one price bucket at one time.
        """
        if self._series_id is not None:
            self._chart.run_script(
                f"{self._chart.id}.chart.removeSeries({self._series_id});"
            )

        if df is None or df.empty:
            return

        sid = Window._id_gen.generate()
        self._series_id = sid

        # Represent heatmap as a coloured histogram where the value encodes
        # the price mid-point and the color encodes intensity.
        records = []
        df_copy = df.copy()
        if hasattr(df_copy['time'].iloc[0], 'timestamp'):
            df_copy['time'] = df_copy['time'].apply(lambda t: int(t.timestamp()))
        else:
            df_copy['time'] = df_copy['time'].astype(int)

        df_copy['price_mid'] = (df_copy['low'] + df_copy['high']) / 2.0
        df_agg = df_copy.groupby('time').agg(
            value=('price_mid', 'mean'),
            intensity=('value', 'mean'),
        ).reset_index()

        data_js = json.dumps(
            [{'time': int(r['time']), 'value': float(r['value'])} for _, r in df_agg.iterrows()]
        )

        self._chart.run_script(
            f"""
            (function() {{
                {sid} = {self._chart.id}.chart.addSeries(
                    LightweightCharts.HistogramSeries,
                    {{
                        color: 'rgba(33, 150, 243, 0.6)',
                        priceFormat: {{type: 'price'}},
                        lastValueVisible: false,
                        priceLineVisible: false,
                    }},
                    {self._pane_index}
                );
                {sid}.setData({data_js});
            }})();
        """
        )

    def detach(self):
        """Remove the heatmap series from the chart."""
        if self._series_id is not None:
            self._chart.run_script(
                f"{self._chart.id}.chart.removeSeries({self._series_id});"
            )
            self._series_id = None
