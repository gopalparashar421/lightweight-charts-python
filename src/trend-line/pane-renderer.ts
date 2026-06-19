import { ViewPoint } from "./pane-view";

import { CanvasRenderingTarget2D } from "fancy-canvas";
import { TwoPointDrawingPaneRenderer } from "../drawing/pane-renderer";
import { DrawingOptions } from "../drawing/options";
import { setLineStyle } from "../helpers/canvas-rendering";
import { drawShapeText, resolveTextColor } from "../helpers/text-rendering";

export class TrendLinePaneRenderer extends TwoPointDrawingPaneRenderer {
    constructor(p1: ViewPoint, p2: ViewPoint, options: DrawingOptions, hovered: boolean) {
        super(p1, p2, options, hovered);
    }

    draw(target: CanvasRenderingTarget2D) {
        target.useBitmapCoordinateSpace(scope => {
            if (
                this._p1.x === null ||
                this._p1.y === null ||
                this._p2.x === null ||
                this._p2.y === null
            )
                return;
            const ctx = scope.context;

            const scaled = this._getScaledCoordinates(scope);
            if (!scaled) return;

            ctx.lineWidth = this._options.width;
            ctx.strokeStyle = this._options.lineColor;
            setLineStyle(ctx, this._options.lineStyle);
            ctx.beginPath();
            ctx.moveTo(scaled.x1, scaled.y1);
            ctx.lineTo(scaled.x2, scaled.y2);
            ctx.stroke();

            const pad = 6 * scope.horizontalPixelRatio;
            const fontSize = Math.round(12 * scope.verticalPixelRatio);
            const color = resolveTextColor(this._options.textColor, this._options.lineColor);
            const dx = scaled.x2 - scaled.x1;
            const dy = scaled.y2 - scaled.y1;
            const length = Math.sqrt(dx * dx + dy * dy) || 1;
            const nx = -dy / length;
            const ny = dx / length;

            let textX: number;
            let textY: number;
            switch (this._options.textPosition) {
                case 'start':
                    textX = scaled.x1 + nx * pad;
                    textY = scaled.y1 + ny * pad;
                    break;
                case 'end':
                    textX = scaled.x2 + nx * pad;
                    textY = scaled.y2 + ny * pad;
                    break;
                default:
                    textX = (scaled.x1 + scaled.x2) / 2 + nx * pad;
                    textY = (scaled.y1 + scaled.y2) / 2 + ny * pad;
                    break;
            }

            drawShapeText(ctx, textX, textY, this._options.text, color, fontSize, 'center', 'middle');

            if (!this._hovered) return;
            this._drawEndCircle(scope, scaled.x1, scaled.y1);
            this._drawEndCircle(scope, scaled.x2, scaled.y2);
        });
    }
}
