import { LineStyle } from "lightweight-charts";

export type BoxTextPosition = 'center' | 'left' | 'right' | 'top' | 'bottom';
export type BoxTextPlacement = 'inside' | 'outside';
export type LineTextPosition = 'above' | 'below';
export type TrendLineTextPosition = 'center' | 'start' | 'end';
export type VerticalTextHAlign = 'left' | 'center' | 'right';
export type VerticalTextVAlign = 'top' | 'center' | 'bottom';

export interface DrawingOptions {
    lineColor: string;
    lineStyle: LineStyle;
    width: number;
    text: string;
    textColor: string;
    axisLabelVisible: boolean;
    textPosition: BoxTextPosition | LineTextPosition | TrendLineTextPosition;
    textHAlign: VerticalTextHAlign;
    textVAlign: VerticalTextVAlign;
}

export const defaultOptions: DrawingOptions = {
    lineColor: '#1E80F0',
    lineStyle: LineStyle.Solid,
    width: 4,
    text: '',
    textColor: '',
    axisLabelVisible: true,
    textPosition: 'center',
    textHAlign: 'center',
    textVAlign: 'center',
};
