import { CanvasRenderingTarget2D } from 'fancy-canvas';
import {
    AutoscaleInfo,
    Coordinate,
    DataChangedScope,
    IPrimitivePaneRenderer,
    IPrimitivePaneView,
    Logical,
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
}

const DEFAULTS: Omit<FullOptions, 'entry' | 'stop' | 'target' | 'entryTime'> = {
    endTime: null,
    stopColor: 'rgba(239, 83, 80, 0.25)',
    targetColor: 'rgba(38, 166, 154, 0.25)',
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

            const x1 = Math.round(d.entryX * hpr);
            const x2 = Math.round(d.endX   * hpr);
            const width = x2 - x1;
            if (width <= 0) return;

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

        // ── Publish to renderer ───────────────────────────────────────────────
        this._renderer.update({
            entryX:         entryXCoord as number,
            endX:           endXCoord   as number,
            entryY:         entryY      as number,
            stopY:          stopY       as number,
            targetY:        targY       as number,
            stopColor:      opts.stopColor,
            targetColor:    opts.targetColor,
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
    }

    public detached(): void {
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
}
