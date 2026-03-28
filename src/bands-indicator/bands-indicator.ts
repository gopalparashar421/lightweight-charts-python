import { CanvasRenderingTarget2D } from 'fancy-canvas';
import {
	AutoscaleInfo,
	Coordinate,
	DataChangedScope,
	ISeriesApi,
	ISeriesPrimitive,
	IPrimitivePaneRenderer,
	IPrimitivePaneView,
	LineData,
	Logical,
	SeriesAttachedParameter,
	SeriesOptionsMap,
	Time,
} from 'lightweight-charts';
import { PluginBase } from '../plugin-base';
import { ClosestTimeIndexFinder } from '../helpers/closest-index';
import { UpperLowerInRange } from '../helpers/min-max-in-range';

interface BandRendererData {
	x: Coordinate | number;
	upper: Coordinate | number;
	lower: Coordinate | number;
}

class BandsIndicatorPaneRenderer implements IPrimitivePaneRenderer {
	_viewData: BandViewData;
	constructor(data: BandViewData) {
		this._viewData = data;
	}
	draw() {}
	drawBackground(target: CanvasRenderingTarget2D) {
		const points: BandRendererData[] = this._viewData.data;
		target.useBitmapCoordinateSpace(scope => {
			const ctx = scope.context;
			ctx.scale(scope.horizontalPixelRatio, scope.verticalPixelRatio);

			ctx.strokeStyle = this._viewData.options.lineColor;
			ctx.lineWidth = this._viewData.options.lineWidth;
			ctx.beginPath();
			const region = new Path2D();
			const lines = new Path2D();
			region.moveTo(points[0].x, points[0].upper);
			lines.moveTo(points[0].x, points[0].upper);
			for (const point of points) {
				region.lineTo(point.x, point.upper);
				lines.lineTo(point.x, point.upper);
			}
			const end = points.length - 1;
			region.lineTo(points[end].x, points[end].lower);
			lines.moveTo(points[end].x, points[end].lower);
			for (let i = points.length - 2; i >= 0; i--) {
				region.lineTo(points[i].x, points[i].lower);
				lines.lineTo(points[i].x, points[i].lower);
			}
			region.lineTo(points[0].x, points[0].upper);
			region.closePath();
			ctx.stroke(lines);
			ctx.fillStyle = this._viewData.options.fillColor;
			ctx.fill(region);
		});
	}
}

interface BandViewData {
	data: BandRendererData[];
	options: Required<BandsIndicatorOptions>;
}

class BandsIndicatorPaneView implements IPrimitivePaneView {
	_source: BandsIndicator;
	_data: BandViewData;

	constructor(source: BandsIndicator) {
		this._source = source;
		this._data = {
			data: [],
			options: this._source._options,
		};
	}

	update() {
		const series = this._source.series;
		const timeScale = this._source.chart.timeScale();
		this._data.data = this._source._bandsData.map(d => {
			return {
				x: timeScale.timeToCoordinate(d.time) ?? -100,
				upper: series.priceToCoordinate(d.upper) ?? -100,
				lower: series.priceToCoordinate(d.lower) ?? -100,
			};
		});
	}

	renderer() {
		return new BandsIndicatorPaneRenderer(this._data);
	}
}

interface BandData {
	time: Time;
	upper: number;
	lower: number;
}

export interface BandsIndicatorOptions {
	lineColor?: string;
	fillColor?: string;
	lineWidth?: number;
}

const defaults: Required<BandsIndicatorOptions> = {
	lineColor: 'rgb(25, 200, 100)',
	fillColor: 'rgba(25, 200, 100, 0.25)',
	lineWidth: 0,
};

export class BandsIndicator extends PluginBase implements ISeriesPrimitive<Time> {
	_paneViews: BandsIndicatorPaneView[];
	_bandsData: BandData[] = [];
	_options: Required<BandsIndicatorOptions>;
	_timeIndices: ClosestTimeIndexFinder<{ time: number }>;
	_upperLower: UpperLowerInRange<BandData>;

	private _upperSeries: ISeriesApi<keyof SeriesOptionsMap>;
	private _lowerSeries: ISeriesApi<keyof SeriesOptionsMap>;

	constructor(
		upperSeries: ISeriesApi<keyof SeriesOptionsMap>,
		lowerSeries: ISeriesApi<keyof SeriesOptionsMap>,
		options: BandsIndicatorOptions = {}
	) {
		super();
		this._upperSeries = upperSeries;
		this._lowerSeries = lowerSeries;
		this._options = { ...defaults, ...options };
		this._paneViews = [new BandsIndicatorPaneView(this)];
		this._timeIndices = new ClosestTimeIndexFinder([]);
		this._upperLower = new UpperLowerInRange([]);
	}

	updateAllViews() {
		this._paneViews.forEach(pw => pw.update());
	}

	paneViews() {
		return this._paneViews;
	}

	attached(p: SeriesAttachedParameter<Time>): void {
		super.attached(p);
		this._lowerSeries.subscribeDataChanged(this._onLowerDataChanged);
		this.dataUpdated('full');
	}

	detached(): void {
		this._lowerSeries.unsubscribeDataChanged(this._onLowerDataChanged);
		super.detached();
	}

	private _onLowerDataChanged = (scope: DataChangedScope) => {
		this.dataUpdated(scope);
		this.requestUpdate();
	};

	dataUpdated(scope: DataChangedScope) {
		this.calculateBands();
		if (scope === 'full') {
			this._timeIndices = new ClosestTimeIndexFinder(
				this._bandsData as unknown as { time: number }[]
			);
		}
	}

	calculateBands() {
		const upperData = this._upperSeries.data();
		const lowerData = this._lowerSeries.data();

		const lowerMap = new Map<Time, number>();
		for (const d of lowerData) {
			const val = (d as LineData).value;
			if (val !== undefined) lowerMap.set(d.time, val);
		}

		const bandData: BandData[] = [];
		for (const d of upperData) {
			const upper = (d as LineData).value;
			if (upper === undefined) continue;
			const lower = lowerMap.get(d.time);
			if (lower === undefined) continue;
			bandData.push({ time: d.time, upper, lower });
		}

		this._bandsData = bandData;
		this._upperLower = new UpperLowerInRange(this._bandsData, 4);
	}

	autoscaleInfo(startTimePoint: Logical, endTimePoint: Logical): AutoscaleInfo {
		const ts = this.chart.timeScale();
		const startTime = (ts.coordinateToTime(
			ts.logicalToCoordinate(startTimePoint) ?? 0
		) ?? 0) as number;
		const endTime = (ts.coordinateToTime(
			ts.logicalToCoordinate(endTimePoint) ?? 5000000000
		) ?? 5000000000) as number;
		const startIndex = this._timeIndices.findClosestIndex(startTime, 'left');
		const endIndex = this._timeIndices.findClosestIndex(endTime, 'right');
		const range = this._upperLower.getMinMax(startIndex, endIndex);
		return {
			priceRange: {
				minValue: range.lower,
				maxValue: range.upper,
			},
		};
	}
}
