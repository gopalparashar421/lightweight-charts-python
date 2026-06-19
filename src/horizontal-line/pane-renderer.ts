import { CanvasRenderingTarget2D } from "fancy-canvas";
import { DrawingOptions } from "../drawing/options";
import { DrawingPaneRenderer } from "../drawing/pane-renderer";
import { ViewPoint } from "../drawing/pane-view";
import { setLineStyle } from "../helpers/canvas-rendering";
import { drawShapeText, resolveTextColor } from "../helpers/text-rendering";

export class HorizontalLinePaneRenderer extends DrawingPaneRenderer {
    _point: ViewPoint = {x: null, y: null};

    constructor(point: ViewPoint, options: DrawingOptions) {
        super(options);
        this._point = point;
    }

    draw(target: CanvasRenderingTarget2D) {
        target.useBitmapCoordinateSpace(scope => {
            if (this._point.y == null) return;
            const ctx = scope.context;

            const scaledY = Math.round(this._point.y * scope.verticalPixelRatio);
            const scaledX = this._point.x ? this._point.x * scope.horizontalPixelRatio : 0;

            ctx.lineWidth = this._options.width;
            ctx.strokeStyle = this._options.lineColor;
            setLineStyle(ctx, this._options.lineStyle);
            ctx.beginPath();

            ctx.moveTo(scaledX, scaledY);
            ctx.lineTo(scope.bitmapSize.width, scaledY);

            ctx.stroke();

            const pad = 6 * scope.verticalPixelRatio;
            const fontSize = Math.round(12 * scope.verticalPixelRatio);
            const color = resolveTextColor(this._options.textColor, this._options.lineColor);
            const textX = (scaledX + scope.bitmapSize.width) / 2;
            const above = this._options.textPosition !== 'below';

            drawShapeText(
                ctx,
                textX,
                above ? scaledY - pad : scaledY + pad,
                this._options.text,
                color,
                fontSize,
                'center',
                above ? 'bottom' : 'top',
            );
        });
    }

}
