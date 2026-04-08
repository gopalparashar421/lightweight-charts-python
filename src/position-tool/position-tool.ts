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
    /** Colour of the dashed entry-price line. */
    entryLineColor?: string;
    /** Colour used for all metric label text. */
    textColor?: string;
    /**
     * Total account balance in the account's base currency.
     * Required to display currency-denominated risk/reward and position size.
     */
    accountBalance?: number | null;
    /**
     * Percentage of the account balance risked on this trade (e.g. `1` = 1 %).
     * Required together with `accountBalance` for currency/size labels.
     */
    riskPercent?: number | null;
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
    entryLineColor: string;
    textColor: string;
    accountBalance: number | null;
    riskPercent: number | null;
}

const DEFAULTS: Omit<FullOptions, 'entry' | 'stop' | 'target' | 'entryTime'> = {
    endTime: null,
    stopColor: 'rgba(239, 83, 80, 0.25)',
    targetColor: 'rgba(38, 166, 154, 0.25)',
    entryLineColor: '#FFD700',
    textColor: 'rgba(255, 255, 255, 0.85)',
    accountBalance: null,
    riskPercent: null,
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
    entryLineColor: string;
    textColor: string;
    stopLabels: string[];
    targetLabels: string[];
    hovered: boolean;
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
     * remain readable at all times.
     */
    draw(target: CanvasRenderingTarget2D): void {
        if (!this._data) return;
        const d = this._data;
        target.useBitmapCoordinateSpace(scope => {
            const ctx = scope.context;
            const hpr = scope.horizontalPixelRatio;
            const vpr = scope.verticalPixelRatio;

            const x1 = Math.round(d.entryX * hpr);
            const x2 = Math.round(d.endX   * hpr);
            const width = x2 - x1;
            if (width <= 0) return;

            const entryY = Math.round(d.entryY  * vpr);
            const stopY  = Math.round(d.stopY   * vpr);
            const targY  = Math.round(d.targetY * vpr);

            // ── Entry dashed line ────────────────────────────────────────────
            ctx.save();
            ctx.strokeStyle = d.entryLineColor;
            ctx.lineWidth   = Math.max(1, Math.round(1.5 * vpr));
            ctx.setLineDash([Math.round(6 * hpr), Math.round(4 * hpr)]);
            ctx.beginPath();
            ctx.moveTo(x1, entryY);
            ctx.lineTo(x2, entryY);
            ctx.stroke();
            ctx.restore();

            // ── Metric labels (only when hovered) ───────────────────────────
            if (!d.hovered) return;

            const scale    = Math.min(hpr, vpr);
            const fontSize = Math.round(11 * scale);
            const lineH    = Math.round(16 * scale);
            const padRight = Math.round(8  * hpr);

            ctx.save();
            ctx.font         = `600 ${fontSize}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
            ctx.textAlign    = 'right';
            ctx.fillStyle    = d.textColor;

            const labelX = x2 - padRight;

            // Stop labels – stack upward from the entry line inside the stop zone
            const stopBottom = Math.max(entryY, stopY);
            const stopTop    = Math.min(entryY, stopY);
            ctx.textBaseline = 'bottom';
            for (let i = d.stopLabels.length - 1; i >= 0; i--) {
                const ly = stopBottom - (d.stopLabels.length - 1 - i) * lineH - Math.round(3 * vpr);
                if (ly - lineH >= stopTop) {
                    ctx.fillText(d.stopLabels[i], labelX, ly);
                }
            }

            // Target labels – stack downward from the entry line inside the target zone
            const targTop    = Math.min(entryY, targY);
            const targBottom = Math.max(entryY, targY);
            ctx.textBaseline = 'top';
            for (let i = 0; i < d.targetLabels.length; i++) {
                const ly = targTop + i * lineH + Math.round(4 * vpr);
                if (ly + lineH <= targBottom) {
                    ctx.fillText(d.targetLabels[i], labelX, ly);
                }
            }

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

        // Minimum offset: entry logical + 5 bars
        const entryLogical = timeScale.coordinateToLogical(entryXCoord) ?? (0 as Logical);
        const minLogical   = (entryLogical + 5) as Logical;

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

        // ── Metrics ───────────────────────────────────────────────────────────
        const riskPts   = Math.abs(opts.entry - opts.stop);
        const rewardPts = Math.abs(opts.target - opts.entry);
        const riskPct   = opts.entry !== 0 ? (riskPts   / opts.entry) * 100 : 0;
        const rewardPct = opts.entry !== 0 ? (rewardPts / opts.entry) * 100 : 0;
        const rrRatio   = riskPts > 0 ? rewardPts / riskPts : 0;

        let accountRisk:    number | null = null;
        let rewardCurrency: number | null = null;
        let quantity:       number | null = null;

        if (opts.accountBalance != null && opts.riskPercent != null && riskPts > 0) {
            accountRisk    = opts.accountBalance * (opts.riskPercent / 100);
            quantity       = accountRisk / riskPts;
            rewardCurrency = accountRisk * rrRatio;
        }

        const f2    = (n: number) => n.toFixed(2);
        const fMny  = (n: number) => n >= 1000 ? `$${(n / 1000).toFixed(2)}K` : `$${n.toFixed(2)}`;

        const stopLabels: string[] = [
            `SL  ${f2(riskPts)} pts  (${f2(riskPct)}%)`,
            ...(accountRisk    != null ? [`Risk  ${fMny(accountRisk)}`]    : []),
            ...(quantity       != null ? [`Qty  ${quantity.toFixed(4)}`]   : []),
        ];

        const targetLabels: string[] = [
            `TP  ${f2(rewardPts)} pts  (${f2(rewardPct)}%)`,
            ...(rewardCurrency != null ? [`Reward  ${fMny(rewardCurrency)}`] : []),
            `R:R  1 : ${f2(rrRatio)}`,
        ];

        // ── Publish to renderer ───────────────────────────────────────────────
        this._renderer.update({
            entryX:         entryXCoord as number,
            endX:           endXCoord   as number,
            entryY:         entryY      as number,
            stopY:          stopY       as number,
            targetY:        targY       as number,
            stopColor:      opts.stopColor,
            targetColor:    opts.targetColor,
            entryLineColor: opts.entryLineColor,
            textColor:      opts.textColor,
            stopLabels,
            targetLabels,
            hovered:        this._source._hovered,
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

    private _paneViews: PositionToolPaneView[];

    constructor(options: PositionToolOptions) {
        super();
        this._options = { ...DEFAULTS, ...options, endTime: options.endTime ?? null } as FullOptions;
        this._paneViews = [new PositionToolPaneView(this)];
    }

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    public attached(param: SeriesAttachedParameter<Time>): void {
        super.attached(param);
        param.chart.subscribeCrosshairMove(this._onCrosshairMove);
    }

    public detached(): void {
        this.chart.unsubscribeCrosshairMove(this._onCrosshairMove);
        super.detached();
    }

    // ── Mouse tracking ────────────────────────────────────────────────────────

    private _onCrosshairMove = (param: MouseEventParams): void => {
        const mousePoint = param.point;
        if (!mousePoint) {
            if (this._hovered) { this._hovered = false; this.requestUpdate(); }
            return;
        }

        const timeScale  = this.chart.timeScale();
        const opts       = this._options;

        const entryXCoord = timeScale.timeToCoordinate(opts.entryTime);
        if (entryXCoord === null) return;

        const entryLogical = timeScale.coordinateToLogical(entryXCoord) ?? (0 as Logical);
        const minLogical   = (entryLogical + 5) as Logical;

        const effectiveEndTime = opts.endTime ?? this._autoEndTime;
        let endXCoord: number;
        if (effectiveEndTime !== null) {
            const rawEnd = timeScale.timeToCoordinate(effectiveEndTime);
            if (rawEnd !== null) {
                const rawLogical = timeScale.coordinateToLogical(rawEnd) ?? (0 as Logical);
                endXCoord = rawLogical < minLogical
                    ? (timeScale.logicalToCoordinate(minLogical) ?? (entryXCoord as number) + 50)
                    : rawEnd as number;
            } else {
                endXCoord = (timeScale.logicalToCoordinate(minLogical) ?? (entryXCoord as number) + 50) as number;
            }
        } else {
            endXCoord = (timeScale.logicalToCoordinate(minLogical) ?? (entryXCoord as number) + 50) as number;
        }

        const entryY = this.series.priceToCoordinate(opts.entry);
        const stopY  = this.series.priceToCoordinate(opts.stop);
        const targY  = this.series.priceToCoordinate(opts.target);
        if (entryY === null || stopY === null || targY === null) return;

        const minY = Math.min(entryY as number, stopY as number, targY as number);
        const maxY = Math.max(entryY as number, stopY as number, targY as number);

        const inside =
            mousePoint.x >= (entryXCoord as number) &&
            mousePoint.x <= endXCoord &&
            mousePoint.y >= minY &&
            mousePoint.y <= maxY;

        if (inside !== this._hovered) {
            this._hovered = inside;
            this.requestUpdate();
        }
    };

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
}
