import { CanvasRenderingTarget2D } from 'fancy-canvas';
import {
    AutoscaleInfo,
    Coordinate,
    DataChangedScope,
    IPrimitivePaneRenderer,
    IPrimitivePaneView,
    Logical,
    MouseEventParams,
    SeriesAttachedParameter,
    Time,
} from 'lightweight-charts';
import { PluginBase } from '../plugin-base';

// ─── Options ────────────────────────────────────────────────────────────────

export interface PositionToolOptions {
    /** Entry (trade open) price. */
    entry: number;
    /** Stop-loss price. */
    stop: number;
    /** Take-profit price. */
    target: number;
    /** Timestamp of the entry bar – left edge of the overlay. */
    entryTime: Time;
    /**
     * Timestamp for the right edge.
     * When `null` (default) the overlay auto-tracks the latest bar on the
     * attached series, always extending at least 5 bars from the entry.
     */
    endTime?: Time | null;
    /** Fill colour for the stop zone (risk rectangle). */
    stopColor?: string;
    /** Fill colour for the target zone (reward rectangle). */
    targetColor?: string;
    /** Number of units/contracts — enables monetary win/lose display. */
    quantity?: number | null;
}

/** Fully resolved options used internally (no optional fields). */
interface FullOptions {
    entry: number;
    stop: number;
    target: number;
    entryTime: Time;
    endTime: Time | null;
    stopColor: string;
    targetColor: string;
    quantity: number | null;
}

const DEFAULTS: Omit<FullOptions, 'entry' | 'stop' | 'target' | 'entryTime'> = {
    endTime: null,
    stopColor: 'rgba(239, 83, 80, 0.25)',
    targetColor: 'rgba(38, 166, 154, 0.25)',
    quantity: null,
};

// ─── Renderer data ───────────────────────────────────────────────────────────

interface RenderData {
    entryX: number;
    endX: number;
    entryY: number;
    stopY: number;
    targetY: number;
    stopColor: string;
    targetColor: string;
    // Hover overlay
    hovered: boolean;
    isLong: boolean;
    rrRatio: string;
    barCount: number;
    winAmount: string;
    loseAmount: string;
    entryPriceLabel: string;
    tpPriceLabel: string;
    slPriceLabel: string;
}

// ─── Overlay bounds (CSS / logical pixels) used for hit-testing ──────────────

interface OverlayBounds {
    entryX: number;
    endX: number;
    minY: number;
    maxY: number;
}

// ─── Drawing helpers ─────────────────────────────────────────────────────────

/** Draw plain text with no background box. All coords are bitmap pixels. */
function _drawText(
    ctx: CanvasRenderingContext2D,
    bmpX: number,
    bmpY: number,
    text: string,
    color: string,
    fontSizePx: number,
    hAlign: CanvasTextAlign,
    vAlign: CanvasTextBaseline,
): void {
    ctx.save();
    ctx.font         = `bold ${fontSizePx}px -apple-system, BlinkMacSystemFont, sans-serif`;
    ctx.fillStyle    = color;
    ctx.textAlign    = hAlign;
    ctx.textBaseline = vAlign;
    ctx.fillText(text, bmpX, bmpY);
    ctx.restore();
}

// ─── Renderer ───────────────────────────────────────────────────────────────

class PositionToolRenderer implements IPrimitivePaneRenderer {
    private _data: RenderData | null = null;

    update(data: RenderData | null): void {
        this._data = data;
    }

    /**
     * Coloured zone rectangles are drawn *behind* the candles so they don't
     * obscure price action.
     */
    drawBackground(target: CanvasRenderingTarget2D): void {
        if (!this._data) return;
        const d = this._data;
        target.useBitmapCoordinateSpace(scope => {
            const ctx = scope.context;
            const hpr = scope.horizontalPixelRatio;
            const vpr = scope.verticalPixelRatio;

            const x1 = Math.round(d.entryX * hpr);
            const x2 = Math.round(d.endX * hpr);
            const width = x2 - x1;
            if (width <= 0) return;

            const entryY = Math.round(d.entryY * vpr);
            const stopY  = Math.round(d.stopY  * vpr);
            const targY  = Math.round(d.targetY * vpr);

            // Stop zone
            ctx.fillStyle = d.stopColor;
            ctx.fillRect(x1, Math.min(entryY, stopY), width, Math.abs(stopY - entryY));

            // Target zone
            ctx.fillStyle = d.targetColor;
            ctx.fillRect(x1, Math.min(entryY, targY), width, Math.abs(targY - entryY));
        });
    }

    /**
     * Entry line and metric labels are drawn *above* the candles so they
     * remain readable at all times. Only rendered while the overlay is hovered.
     */
    draw(target: CanvasRenderingTarget2D): void {
        if (!this._data?.hovered) return;
        const d = this._data;
        target.useBitmapCoordinateSpace(scope => {
            const ctx = scope.context;
            const hpr = scope.horizontalPixelRatio;
            const vpr = scope.verticalPixelRatio;

            const x1     = Math.round(d.entryX  * hpr);
            const x2     = Math.round(d.endX    * hpr);
            const width  = x2 - x1;
            if (width <= 0) return;

            const entryY = Math.round(d.entryY  * vpr);
            const stopY  = Math.round(d.stopY   * vpr);
            const targY  = Math.round(d.targetY * vpr);
            const midX   = Math.round((x1 + x2) / 2);

            // Scale font with horizontal pixel ratio for crisp high-DPI text
            const fontSize = Math.round(11 * hpr);

            const pad = Math.round(4 * hpr);

            ctx.save();

            // ── Entry price line (blue) ───────────────────────────────────────
            ctx.strokeStyle = '#2962FF';
            ctx.lineWidth   = Math.round(1 * vpr);
            ctx.beginPath();
            ctx.moveTo(x1, entryY);
            ctx.lineTo(x2, entryY);
            ctx.stroke();

            // ── Entry price label (left inside rectangle, above entry line) ────
            _drawText(ctx, x1 + pad, entryY - pad, d.entryPriceLabel,
                '#2962FF', fontSize, 'left', 'bottom');

            // ── Bar count label (right inside rectangle, above entry line) ─────
            _drawText(ctx, x2 - pad, entryY - pad, `${d.barCount} bars`,
                'rgba(255,255,255,0.9)', fontSize, 'right', 'bottom');

            // ── R:R label (centre, below entry line) ──────────────────────────
            _drawText(ctx, midX, entryY + pad, d.rrRatio,
                'rgba(255,255,255,0.9)', fontSize, 'center', 'top');

            // Zone labels: anchored inside each rectangle near the far edge.
            // Long:  targY < entryY (target zone above), stopY > entryY (stop zone below)
            // Short: targY > entryY (target zone below), stopY < entryY (stop zone above)
            const tpLabelY: number   = d.isLong ? (targY + pad) : (targY - pad);
            const slLabelY: number   = d.isLong ? (stopY - pad) : (stopY + pad);
            const tpVAlign: CanvasTextBaseline = d.isLong ? 'top'    : 'bottom';
            const slVAlign: CanvasTextBaseline = d.isLong ? 'bottom' : 'top';

            // ── TP price label (left inside target zone) ──────────────────────
            _drawText(ctx, x1 + pad, tpLabelY, d.tpPriceLabel,
                'rgba(38,166,154,1)', fontSize, 'left', tpVAlign);

            // ── Win amount label (right inside target zone) ───────────────────
            _drawText(ctx, x2 - pad, tpLabelY, d.winAmount,
                'rgba(38,166,154,1)', fontSize, 'right', tpVAlign);

            // ── SL price label (left inside stop zone) ────────────────────────
            _drawText(ctx, x1 + pad, slLabelY, d.slPriceLabel,
                'rgba(239,83,80,1)', fontSize, 'left', slVAlign);

            // ── Lose amount label (right inside stop zone) ────────────────────
            _drawText(ctx, x2 - pad, slLabelY, d.loseAmount,
                'rgba(239,83,80,1)', fontSize, 'right', slVAlign);

            ctx.restore();
        });
    }
}

// ─── Pane view ───────────────────────────────────────────────────────────────

class PositionToolPaneView implements IPrimitivePaneView {
    private _source: PositionTool;
    private _renderer: PositionToolRenderer;

    constructor(source: PositionTool) {
        this._source   = source;
        this._renderer = new PositionToolRenderer();
    }

    update(): void {
        const opts      = this._source._options;
        const chart     = this._source.chart;
        const series    = this._source.series;
        const timeScale = chart.timeScale();

        // ── X coordinates ────────────────────────────────────────────────────
        const entryXCoord = timeScale.timeToCoordinate(opts.entryTime);
        if (entryXCoord === null) { this._renderer.update(null); return; }

        // Determine effective end time (pinned or auto-tracked)
        const effectiveEndTime = opts.endTime ?? this._source._autoEndTime;

        // Minimum offset: entry logical + 15 bars
        const entryLogical = timeScale.coordinateToLogical(entryXCoord) ?? (0 as Logical);
        const minLogical   = (entryLogical + 15) as Logical;

        let endXCoord: Coordinate;
        if (effectiveEndTime !== null) {
            const rawEnd = timeScale.timeToCoordinate(effectiveEndTime);
            if (rawEnd !== null) {
                const rawLogical = timeScale.coordinateToLogical(rawEnd) ?? (0 as Logical);
                endXCoord = (rawLogical < minLogical)
                    ? (timeScale.logicalToCoordinate(minLogical) ?? ((entryXCoord as number) + 50) as Coordinate)
                    : rawEnd;
            } else {
                endXCoord = (timeScale.logicalToCoordinate(minLogical) ?? ((entryXCoord as number) + 50)) as Coordinate;
            }
        } else {
            endXCoord = (timeScale.logicalToCoordinate(minLogical) ?? ((entryXCoord as number) + 50)) as Coordinate;
        }

        // ── Y coordinates ────────────────────────────────────────────────────
        const entryY = series.priceToCoordinate(opts.entry);
        const stopY  = series.priceToCoordinate(opts.stop);
        const targY  = series.priceToCoordinate(opts.target);
        if (entryY === null || stopY === null || targY === null) {
            this._renderer.update(null);
            return;
        }

        // ── Computed hover metrics ────────────────────────────────────────────
        const riskPts   = Math.abs(opts.entry - opts.stop);
        const rewardPts = Math.abs(opts.target - opts.entry);
        const rrRatio   = riskPts > 0 ? `1:${Math.round(rewardPts / riskPts)}` : '1:∞';

        const endLogical = timeScale.coordinateToLogical(endXCoord) ?? minLogical;
        const barCount   = Math.max(0, (endLogical as number) - (entryLogical as number));

        const formatPrice = (p: number) => `$${p.toFixed(2)}`;
        const formatDelta = (pts: number, sign: '+' | '-') =>
            `${sign}${Math.abs(pts).toFixed(2)}`;
        const formatMoney = (pts: number, sign: '+' | '-') => {
            const amt = Math.abs(pts * (opts.quantity as number));
            return `${sign}$${amt.toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
            })}`;
        };

        const winAmount  = opts.quantity !== null
            ? formatMoney(rewardPts, '+')
            : formatDelta(rewardPts, '+');
        const loseAmount = opts.quantity !== null
            ? formatMoney(riskPts, '-')
            : formatDelta(riskPts, '-');

        // ── Store pixel bounds for hover hit-testing ──────────────────────────
        this._source._lastBounds = {
            entryX: entryXCoord as number,
            endX:   endXCoord   as number,
            minY:   Math.min(stopY as number, targY as number),
            maxY:   Math.max(stopY as number, targY as number),
        };

        // ── Publish to renderer ───────────────────────────────────────────────
        this._renderer.update({
            entryX:          entryXCoord as number,
            endX:            endXCoord   as number,
            entryY:          entryY      as number,
            stopY:           stopY       as number,
            targetY:         targY       as number,
            stopColor:       opts.stopColor,
            targetColor:     opts.targetColor,
            hovered:         this._source._hovered,
            isLong:          opts.target > opts.entry,
            rrRatio,
            barCount,
            winAmount,
            loseAmount,
            entryPriceLabel: formatPrice(opts.entry),
            tpPriceLabel:    formatPrice(opts.target),
            slPriceLabel:    formatPrice(opts.stop),  // $ prefix applied by formatPrice
        });
    }

    renderer(): IPrimitivePaneRenderer {
        return this._renderer;
    }
}

// ─── Main plugin class ───────────────────────────────────────────────────────

export class PositionTool extends PluginBase {
    _options: FullOptions;
    /** Latest bar time tracked automatically when `endTime` is null. */
    _autoEndTime: Time | null = null;
    /** True when the mouse pointer is inside the overlay bounds. */
    _hovered: boolean = false;
    /** Last-computed overlay bounds in CSS pixels, used for hover hit-testing. */
    _lastBounds: OverlayBounds | null = null;

    private _paneViews: PositionToolPaneView[];
    private _subscribed: boolean = false;

    constructor(options: PositionToolOptions) {
        super();
        this._options = { ...DEFAULTS, ...options, endTime: options.endTime ?? null } as FullOptions;
        this._paneViews = [new PositionToolPaneView(this)];
    }

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    public attached(param: SeriesAttachedParameter<Time>): void {
        super.attached(param);
        if (!this._subscribed) {
            this.chart.subscribeCrosshairMove(this._crosshairMoveHandler);
            this._subscribed = true;
        }
    }

    public detached(): void {
        if (this._subscribed) {
            this.chart.unsubscribeCrosshairMove(this._crosshairMoveHandler);
            this._subscribed = false;
        }
        super.detached();
    }

    // ── ISeriesPrimitive ──────────────────────────────────────────────────────

    updateAllViews(): void {
        this._paneViews.forEach(v => v.update());
    }

    paneViews(): readonly IPrimitivePaneView[] {
        return this._paneViews;
    }

    /**
     * Ensure the chart autoscale always keeps stop, entry and target in view.
     * This prevents `priceToCoordinate` from returning null for off-screen prices,
     * which was causing the stop-zone rectangle to disappear.
     */
    autoscaleInfo(_startTimePoint: Logical, _endTimePoint: Logical): AutoscaleInfo | null {
        const { entry, stop, target } = this._options;
        return {
            priceRange: {
                minValue: Math.min(entry, stop, target),
                maxValue: Math.max(entry, stop, target),
            },
        };
    }

    applyOptions(options: Partial<PositionToolOptions>): void {
        this._options = {
            ...this._options,
            ...options,
            endTime: options.endTime !== undefined ? (options.endTime ?? null) : this._options.endTime,
        };
        this.requestUpdate();
    }

    protected dataUpdated(_scope: DataChangedScope): void {
        // Keep the auto-tracked end time in sync with new/updated bars
        const data = this.series.data();
        if (data.length > 0) {
            this._autoEndTime = (data[data.length - 1] as { time: Time }).time;
        }
        this.requestUpdate();
    }

    // ── Hover detection ───────────────────────────────────────────────────────

    private _crosshairMoveHandler = (param: MouseEventParams): void => {
        const bounds = this._lastBounds;
        if (!bounds || !param.point) {
            if (this._hovered) {
                this._hovered = false;
                this.requestUpdate();
            }
            return;
        }
        const { x, y } = param.point;
        const inside =
            x >= bounds.entryX && x <= bounds.endX &&
            y >= bounds.minY   && y <= bounds.maxY;
        if (inside !== this._hovered) {
            this._hovered = inside;
            this.requestUpdate();
        }
    };
}
