import { CanvasRenderingTarget2D } from "fancy-canvas";
import { DrawingOptions } from "../drawing/options";
import { DrawingPaneRenderer } from "../drawing/pane-renderer";
import { ViewPoint } from "../drawing/pane-view";
import { setLineStyle } from "../helpers/canvas-rendering";
import { drawShapeText, resolveTextColor } from "../helpers/text-rendering";

export class VerticalLinePaneRenderer extends DrawingPaneRenderer {
    _point: ViewPoint = {x: null, y: null};

    constructor(point: ViewPoint, options: DrawingOptions) {
        super(options);
        this._point = point;
    }

    draw(target: CanvasRenderingTarget2D) {
        target.useBitmapCoordinateSpace(scope => {
            if (this._point.x == null) return;
            const ctx = scope.context;
            const scaledX = this._point.x * scope.horizontalPixelRatio;

            ctx.lineWidth = this._options.width;
            ctx.strokeStyle = this._options.lineColor;
            setLineStyle(ctx, this._options.lineStyle);

            ctx.beginPath();
            ctx.moveTo(scaledX, 0);
            ctx.lineTo(scaledX, scope.bitmapSize.height);
            ctx.stroke();

            const pad = 6 * scope.horizontalPixelRatio;
            const fontSize = Math.round(12 * scope.verticalPixelRatio);
            const color = resolveTextColor(this._options.textColor, this._options.lineColor);
            const height = scope.bitmapSize.height;

            let textY: number;
            let vAlign: CanvasTextBaseline;
            switch (this._options.textVAlign) {
                case 'top':
                    textY = pad;
                    vAlign = 'top';
                    break;
                case 'bottom':
                    textY = height - pad;
                    vAlign = 'bottom';
                    break;
                default:
                    textY = height / 2;
                    vAlign = 'middle';
                    break;
            }

            let textX: number;
            let hAlign: CanvasTextAlign;
            switch (this._options.textHAlign) {
                case 'left':
                    textX = scaledX - pad;
                    hAlign = 'right';
                    break;
                case 'right':
                    textX = scaledX + pad;
                    hAlign = 'left';
                    break;
                default:
                    textX = scaledX;
                    hAlign = 'center';
                    break;
            }

            drawShapeText(ctx, textX, textY, this._options.text, color, fontSize, hAlign, vAlign);
        });
    }

}
