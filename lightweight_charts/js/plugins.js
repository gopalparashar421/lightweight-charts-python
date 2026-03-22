/**
 * lightweight-charts-python plugin library
 * Exposes Lib.Plugins namespace with SessionHighlighting, Tooltip,
 * BandsIndicator, VolumeProfile, and HeatmapSeries plugin implementations.
 */
(function () {
    if (!window.Lib) window.Lib = {};
    Lib.Plugins = {};

    // =========================================================================
    // Helpers
    // =========================================================================

    function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

    function lerp(a, b, t) { return a + (b - a) * t; }

    function hexToRgb(hex) {
        var r = parseInt(hex.slice(1, 3), 16);
        var g = parseInt(hex.slice(3, 5), 16);
        var b = parseInt(hex.slice(5, 7), 16);
        return { r: r, g: g, b: b };
    }

    // =========================================================================
    // SessionHighlighting
    // =========================================================================

    /**
     * A series primitive that highlights the chart background for given time
     * ranges (e.g. trading sessions).
     *
     * Usage:
     *   const plugin = new Lib.Plugins.SessionHighlighting({ sessionColor: 'rgba(41,98,255,0.08)' });
     *   series.attachPrimitive(plugin);
     *   plugin.setData([{ start: 1700000000, end: 1700003600 }]);
     */
    class SessionHighlightingPaneRenderer {
        constructor(sessions, timeScale, defaultColor) {
            this._sessions = sessions;
            this._timeScale = timeScale;
            this._defaultColor = defaultColor;
        }

        draw(target) {
            if (!this._sessions || this._sessions.length === 0) return;
            const timeScale = this._timeScale;
            target.useBitmapCoordinateSpace(function (scope) {
                var ctx = scope.context;
                var h = scope.bitmapSize.height;
                var hr = scope.horizontalPixelRatio;
                ctx.save();
                for (var i = 0; i < this._sessions.length; i++) {
                    var session = this._sessions[i];
                    var x1 = timeScale.timeToCoordinate(session.start);
                    var x2 = timeScale.timeToCoordinate(session.end);
                    if (x1 === null || x2 === null) continue;
                    var left = Math.round(Math.min(x1, x2) * hr);
                    var width = Math.round(Math.abs(x2 - x1) * hr);
                    if (width <= 0) continue;
                    ctx.fillStyle = session.color || this._defaultColor;
                    ctx.fillRect(left, 0, width, h);
                }
                ctx.restore();
            }.bind(this));
        }
    }

    class SessionHighlightingPaneView {
        constructor(source) {
            this._source = source;
        }

        update() {}

        renderer() {
            return new SessionHighlightingPaneRenderer(
                this._source._sessions,
                this._source._chart && this._source._chart.timeScale(),
                this._source._sessionColor
            );
        }

        zOrder() { return 'bottom'; }
    }

    class SessionHighlighting {
        constructor(options) {
            options = options || {};
            this._sessionColor = options.sessionColor || 'rgba(41, 98, 255, 0.08)';
            this._sessions = [];
            this._paneView = new SessionHighlightingPaneView(this);
            this._chart = null;
            this._series = null;
            this._requestUpdate = null;
        }

        attached(params) {
            this._chart = params.chart;
            this._series = params.series;
            this._requestUpdate = params.requestUpdate;
            if (this._requestUpdate) this._requestUpdate();
        }

        detached() {
            this._chart = null;
            this._series = null;
            this._requestUpdate = null;
        }

        paneViews() { return [this._paneView]; }

        updateAllViews() { this._paneView.update(); }

        setData(sessions) {
            this._sessions = sessions || [];
            if (this._requestUpdate) this._requestUpdate();
        }

        applyOptions(options) {
            if (options.sessionColor !== undefined) this._sessionColor = options.sessionColor;
            if (this._requestUpdate) this._requestUpdate();
        }
    }

    Lib.Plugins.SessionHighlighting = SessionHighlighting;

    // =========================================================================
    // Tooltip
    // =========================================================================

    /**
     * A floating tooltip showing OHLCV or value data near the crosshair.
     *
     * Usage:
     *   const tooltip = new Lib.Plugins.Tooltip({ title: 'AAPL', fontSize: 12 });
     *   series.attachPrimitive(tooltip);
     */
    class Tooltip {
        constructor(options) {
            options = options || {};
            this._title = options.title || '';
            this._fontSize = options.fontSize || 12;
            this._color = options.color || 'rgba(255,255,255,0.9)';
            this._background = options.background || 'rgba(15,15,15,0.8)';
            this._chart = null;
            this._series = null;
            this._tooltipEl = null;
            this._boundOnCrosshairMove = null;
        }

        attached(params) {
            this._chart = params.chart;
            this._series = params.series;
            this._createTooltipElement();
            this._boundOnCrosshairMove = this._onCrosshairMove.bind(this);
            this._chart.subscribeCrosshairMove(this._boundOnCrosshairMove);
        }

        detached() {
            if (this._chart && this._boundOnCrosshairMove) {
                this._chart.unsubscribeCrosshairMove(this._boundOnCrosshairMove);
            }
            if (this._tooltipEl && this._tooltipEl.parentNode) {
                this._tooltipEl.parentNode.removeChild(this._tooltipEl);
            }
            this._chart = null;
            this._series = null;
            this._tooltipEl = null;
        }

        paneViews() { return []; }

        updateAllViews() {}

        _createTooltipElement() {
            var container = this._chart.chartElement ? this._chart.chartElement().parentNode : document.getElementById('container');
            this._tooltipEl = document.createElement('div');
            this._tooltipEl.style.cssText = [
                'position:absolute',
                'display:none',
                'padding:6px 8px',
                'pointer-events:none',
                'z-index:1000',
                'font-size:' + this._fontSize + 'px',
                'color:' + this._color,
                'background:' + this._background,
                'border-radius:4px',
                'border:1px solid rgba(255,255,255,0.1)',
                'white-space:nowrap',
            ].join(';');
            container.style.position = container.style.position || 'relative';
            container.appendChild(this._tooltipEl);
        }

        _onCrosshairMove(param) {
            if (!this._tooltipEl) return;
            if (!param.point || !param.time) {
                this._tooltipEl.style.display = 'none';
                return;
            }
            var data = param.seriesData && param.seriesData.get(this._series);
            if (!data) {
                this._tooltipEl.style.display = 'none';
                return;
            }

            var html = '';
            if (this._title) {
                html += '<div style="font-weight:bold;margin-bottom:4px">' + this._title + '</div>';
            }
            if (typeof data.open !== 'undefined') {
                html += '<div>O: ' + (+data.open).toFixed(2) + '</div>';
                html += '<div>H: ' + (+data.high).toFixed(2) + '</div>';
                html += '<div>L: ' + (+data.low).toFixed(2) + '</div>';
                html += '<div>C: ' + (+data.close).toFixed(2) + '</div>';
                if (typeof data.volume !== 'undefined') {
                    html += '<div>V: ' + (+data.volume).toFixed(0) + '</div>';
                }
            } else if (typeof data.value !== 'undefined') {
                html += '<div>Value: ' + (+data.value).toFixed(2) + '</div>';
            }

            this._tooltipEl.innerHTML = html;
            this._tooltipEl.style.display = 'block';

            var container = this._tooltipEl.parentNode;
            var cw = container.clientWidth || 300;
            var ch = container.clientHeight || 200;
            var tw = this._tooltipEl.offsetWidth + 20;
            var th = this._tooltipEl.offsetHeight + 20;
            var left = param.point.x + 15;
            var top = param.point.y - th / 2;
            if (left + tw > cw) left = param.point.x - tw;
            if (top < 0) top = 5;
            if (top + th > ch) top = ch - th - 5;
            this._tooltipEl.style.left = left + 'px';
            this._tooltipEl.style.top = top + 'px';
        }

        applyOptions(options) {
            if (options.title !== undefined) this._title = options.title;
            if (options.fontSize !== undefined) this._fontSize = options.fontSize;
            if (options.color !== undefined) this._color = options.color;
            if (options.background !== undefined) this._background = options.background;
        }
    }

    Lib.Plugins.Tooltip = Tooltip;

    // =========================================================================
    // BandsIndicator
    // =========================================================================

    /**
     * Draws a filled band between an upper and lower series.
     *
     * Usage:
     *   const bands = new Lib.Plugins.BandsIndicator(
     *     upperSeries, lowerSeries,
     *     { fillColor: 'rgba(33,150,243,0.1)', lineWidth: 1 }
     *   );
     *   upperSeries.attachPrimitive(bands);
     */
    class BandsIndicatorPaneRenderer {
        constructor(upperPoints, lowerPoints, options) {
            this._upperPoints = upperPoints || [];
            this._lowerPoints = lowerPoints || [];
            this._options = options;
        }

        draw(target) {
            var up = this._upperPoints;
            var lo = this._lowerPoints;
            if (!up.length || !lo.length) return;
            target.useBitmapCoordinateSpace(function (scope) {
                var ctx = scope.context;
                var hr = scope.horizontalPixelRatio;
                var vr = scope.verticalPixelRatio;
                ctx.save();

                // Build a path along upper then reversed lower to form a closed shape
                ctx.beginPath();
                ctx.moveTo(up[0].x * hr, up[0].y * vr);
                for (var i = 1; i < up.length; i++) {
                    ctx.lineTo(up[i].x * hr, up[i].y * vr);
                }
                for (var j = lo.length - 1; j >= 0; j--) {
                    ctx.lineTo(lo[j].x * hr, lo[j].y * vr);
                }
                ctx.closePath();
                ctx.fillStyle = this._options.fillColor || 'rgba(33,150,243,0.1)';
                ctx.fill();
                ctx.restore();
            }.bind(this));
        }
    }

    class BandsIndicatorPaneView {
        constructor(source) {
            this._source = source;
            this._upperPoints = [];
            this._lowerPoints = [];
        }

        update() {
            if (!this._source._chart) return;
            var timeScale = this._source._chart.timeScale();
            var upperSeries = this._source._upperSeries;
            var lowerSeries = this._source._lowerSeries;

            var upperData = upperSeries.data ? upperSeries.data() : [];
            var lowerData = lowerSeries.data ? lowerSeries.data() : [];

            this._upperPoints = this._buildPoints(upperData, timeScale, upperSeries);
            this._lowerPoints = this._buildPoints(lowerData, timeScale, lowerSeries);
        }

        _buildPoints(data, timeScale, series) {
            var points = [];
            for (var i = 0; i < data.length; i++) {
                var d = data[i];
                var x = timeScale.timeToCoordinate(d.time);
                var y = series.priceToCoordinate(d.value !== undefined ? d.value : d.close);
                if (x !== null && y !== null) {
                    points.push({ x: x, y: y });
                }
            }
            return points;
        }

        renderer() {
            return new BandsIndicatorPaneRenderer(
                this._upperPoints,
                this._lowerPoints,
                this._source._options
            );
        }
    }

    class BandsIndicator {
        constructor(upperSeries, lowerSeries, options) {
            options = options || {};
            this._upperSeries = upperSeries;
            this._lowerSeries = lowerSeries;
            this._options = {
                fillColor: options.fillColor || 'rgba(33,150,243,0.1)',
                upperColor: options.upperColor || '#2196F3',
                lowerColor: options.lowerColor || '#2196F3',
                lineWidth: options.lineWidth !== undefined ? options.lineWidth : 1,
            };
            this._paneView = new BandsIndicatorPaneView(this);
            this._chart = null;
            this._requestUpdate = null;
        }

        attached(params) {
            this._chart = params.chart;
            this._requestUpdate = params.requestUpdate;
            if (this._requestUpdate) this._requestUpdate();
        }

        detached() {
            this._chart = null;
            this._requestUpdate = null;
        }

        paneViews() { return [this._paneView]; }

        updateAllViews() { this._paneView.update(); }

        applyOptions(options) {
            if (options.fillColor !== undefined) this._options.fillColor = options.fillColor;
            if (options.upperColor !== undefined) this._options.upperColor = options.upperColor;
            if (options.lowerColor !== undefined) this._options.lowerColor = options.lowerColor;
            if (options.lineWidth !== undefined) this._options.lineWidth = options.lineWidth;
            if (this._requestUpdate) this._requestUpdate();
        }
    }

    Lib.Plugins.BandsIndicator = BandsIndicator;

    // =========================================================================
    // VolumeProfile
    // =========================================================================

    /**
     * Displays a volume profile (price histogram) overlaid on the chart.
     *
     * Usage:
     *   const vp = new Lib.Plugins.VolumeProfile({ upColor: 'rgba(38,166,154,0.5)', widthFactor: 0.4 });
     *   series.attachPrimitive(vp);
     *   vp.setData(ohlcvRecords);
     */
    class VolumeProfilePaneRenderer {
        constructor(bars, priceConverter, options, chartWidth) {
            this._bars = bars || [];
            this._priceConverter = priceConverter;
            this._options = options;
            this._chartWidth = chartWidth || 200;
        }

        draw(target) {
            if (!this._bars.length || !this._priceConverter) return;
            var bars = this._bars;
            var opts = this._options;
            var widthFactor = opts.widthFactor !== undefined ? opts.widthFactor : 0.4;
            var priceConv = this._priceConverter;
            var chartWidth = this._chartWidth;

            // Build a price-bucketed histogram
            var buckets = {};
            var maxVol = 0;
            for (var i = 0; i < bars.length; i++) {
                var b = bars[i];
                var mid = (b.high + b.low) / 2;
                var key = mid.toFixed(2);
                if (!buckets[key]) buckets[key] = { price: mid, upVol: 0, downVol: 0 };
                var isUp = b.close >= b.open;
                if (isUp) {
                    buckets[key].upVol += (b.volume || 0);
                } else {
                    buckets[key].downVol += (b.volume || 0);
                }
                var total = buckets[key].upVol + buckets[key].downVol;
                if (total > maxVol) maxVol = total;
            }

            var bucketList = Object.values(buckets);
            if (!bucketList.length || !maxVol) return;

            target.useBitmapCoordinateSpace(function (scope) {
                var ctx = scope.context;
                var hr = scope.horizontalPixelRatio;
                var vr = scope.verticalPixelRatio;
                var bw = scope.bitmapSize.width;
                var barHeightPx = Math.max(1, 2 * vr);

                ctx.save();
                for (var i = 0; i < bucketList.length; i++) {
                    var bucket = bucketList[i];
                    var y = priceConv(bucket.price);
                    if (y === null) continue;
                    var yPx = Math.round(y * vr);
                    var totalVol = bucket.upVol + bucket.downVol;
                    var totalW = Math.round((totalVol / maxVol) * widthFactor * bw);
                    var upW = totalVol > 0 ? Math.round((bucket.upVol / totalVol) * totalW) : 0;
                    var downW = totalW - upW;
                    var startX = bw - totalW;

                    // up portion
                    ctx.fillStyle = opts.upColor || 'rgba(38,166,154,0.5)';
                    ctx.fillRect(startX, yPx - barHeightPx / 2, upW, barHeightPx);
                    // down portion
                    ctx.fillStyle = opts.downColor || 'rgba(239,83,80,0.5)';
                    ctx.fillRect(startX + upW, yPx - barHeightPx / 2, downW, barHeightPx);
                }
                ctx.restore();
            }.bind(this));
        }
    }

    class VolumeProfilePaneView {
        constructor(source) {
            this._source = source;
            this._priceConverter = null;
            this._chartWidth = 200;
        }

        update() {}

        renderer() {
            return new VolumeProfilePaneRenderer(
                this._source._data,
                this._priceConverter,
                this._source._options,
                this._chartWidth
            );
        }
    }

    class VolumeProfile {
        constructor(options) {
            options = options || {};
            this._options = {
                upColor: options.upColor || 'rgba(38,166,154,0.5)',
                downColor: options.downColor || 'rgba(239,83,80,0.5)',
                widthFactor: options.widthFactor !== undefined ? options.widthFactor : 0.4,
            };
            this._data = [];
            this._paneView = new VolumeProfilePaneView(this);
            this._chart = null;
            this._series = null;
            this._requestUpdate = null;
        }

        attached(params) {
            this._chart = params.chart;
            this._series = params.series;
            this._requestUpdate = params.requestUpdate;
            if (this._requestUpdate) this._requestUpdate();
        }

        detached() {
            this._chart = null;
            this._series = null;
            this._requestUpdate = null;
        }

        paneViews() { return [this._paneView]; }

        updateAllViews() {
            if (this._series) {
                this._paneView._priceConverter = this._series.priceToCoordinate.bind(this._series);
            }
            if (this._chart) {
                this._paneView._chartWidth = this._chart.chartElement
                    ? this._chart.chartElement().clientWidth
                    : 500;
            }
            this._paneView.update();
        }

        setData(records) {
            this._data = records || [];
            if (this._requestUpdate) this._requestUpdate();
        }

        applyOptions(options) {
            Object.assign(this._options, options);
            if (this._requestUpdate) this._requestUpdate();
        }
    }

    Lib.Plugins.VolumeProfile = VolumeProfile;

    // =========================================================================
    // HeatmapSeries (custom series pane view)
    // =========================================================================

    /**
     * A custom series pane view that renders a heatmap (e.g. orderbook/price-level
     * intensity map). Each data point is { time, low, high, value }.
     *
     * Usage:
     *   const heatmapView = new Lib.Plugins.HeatmapSeries({ colorScale: [...] });
     *   const heatmapSeries = chart.addCustomSeries(heatmapView, {}, paneIndex);
     */
    class HeatmapSeriesPaneRenderer {
        constructor(data, options, priceConverter, timeConverter) {
            this._data = data || [];
            this._options = options || {};
            this._priceConverter = priceConverter;
            this._timeConverter = timeConverter;
        }

        draw(target) {
            if (!this._data.length) return;
            var priceConv = this._priceConverter;
            var timeConv = this._timeConverter;
            var colorScale = this._options.colorScale;

            target.useBitmapCoordinateSpace(function (scope) {
                var ctx = scope.context;
                var hr = scope.horizontalPixelRatio;
                var vr = scope.verticalPixelRatio;
                ctx.save();
                for (var i = 0; i < this._data.length; i++) {
                    var d = this._data[i];
                    var x = timeConv(d.time);
                    var y1 = priceConv(d.high);
                    var y2 = priceConv(d.low);
                    if (x === null || y1 === null || y2 === null) continue;
                    var xPx = Math.round(x * hr);
                    var yTop = Math.round(Math.min(y1, y2) * vr);
                    var yBot = Math.round(Math.max(y1, y2) * vr);
                    var cellH = Math.max(1, yBot - yTop);
                    ctx.fillStyle = this._valueToColor(d.value, colorScale);
                    ctx.fillRect(xPx - hr, yTop, hr * 2, cellH);
                }
                ctx.restore();
            }.bind(this));
        }

        _valueToColor(value, colorScale) {
            if (!colorScale || colorScale.length < 2) {
                var alpha = clamp(value, 0, 1);
                return 'rgba(33,150,243,' + alpha + ')';
            }
            var t = clamp(value, 0, 1) * (colorScale.length - 1);
            var lo = Math.floor(t);
            var hi = Math.min(lo + 1, colorScale.length - 1);
            var f = t - lo;
            var ca = colorScale[lo];
            var cb = colorScale[hi];
            if (typeof ca === 'string') {
                ca = this._parseColor(ca);
            }
            if (typeof cb === 'string') {
                cb = this._parseColor(cb);
            }
            var r = Math.round(lerp(ca[0], cb[0], f));
            var g = Math.round(lerp(ca[1], cb[1], f));
            var b = Math.round(lerp(ca[2], cb[2], f));
            var a = lerp(ca[3] !== undefined ? ca[3] : 1, cb[3] !== undefined ? cb[3] : 1, f);
            return 'rgba(' + r + ',' + g + ',' + b + ',' + a + ')';
        }

        _parseColor(s) {
            var m = s.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
            if (m) return [+m[1], +m[2], +m[3], m[4] !== undefined ? +m[4] : 1];
            if (s.charAt(0) === '#') {
                var rgb = hexToRgb(s);
                return [rgb.r, rgb.g, rgb.b, 1];
            }
            return [33, 150, 243, 1];
        }
    }

    class HeatmapSeriesPaneView {
        constructor() {
            this._data = [];
            this._options = {};
            this._priceConverter = null;
            this._timeConverter = null;
        }

        update(data, series) {
            this._data = data;
            if (series) {
                this._priceConverter = series.priceToCoordinate.bind(series);
            }
        }

        renderer() {
            return new HeatmapSeriesPaneRenderer(
                this._data,
                this._options,
                this._priceConverter,
                this._timeConverter
            );
        }
    }

    class HeatmapSeries {
        constructor(options) {
            options = options || {};
            this._options = {
                colorScale: options.colorScale || null,
            };
            this._paneView = new HeatmapSeriesPaneView();
        }

        priceValueBuilder(plotRow) {
            return [plotRow.high, plotRow.low, plotRow.value];
        }

        isWhitespace(data) {
            return data.value === undefined || data.value === null;
        }

        renderer() {
            return this._paneView.renderer();
        }

        update(data, series) {
            this._paneView.update(data, series);
        }

        defaultOptions() {
            return Object.assign({}, this._options);
        }

        paneViews() {
            return [this._paneView];
        }

        // Called by LWC to get the renderer for the entire data set
        customSeriesPlotValuesBuilder(plotRow) {
            return {
                customValues: { low: plotRow.low, high: plotRow.high },
                value: plotRow.value,
            };
        }
    }

    Lib.Plugins.HeatmapSeries = HeatmapSeries;

})();
