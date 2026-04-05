import { CustomData } from 'lightweight-charts';

export interface HeatmapCell {
	// Price for the lower edge of the heatmap cell
	low: number;
	// Price for the upper edge of the heatmap cell
	high: number;
	// Amount for the cell
	amount: number;
	// Optional explicit CSS color; overrides all shaders when provided
	color?: string;
	// Optional side identifier ('bid' | 'ask'); selects bidShader / askShader
	side?: string;
}

/**
 * HeatMap Series Data
 */
export interface HeatMapData extends CustomData {
	cells: HeatmapCell[];
}
