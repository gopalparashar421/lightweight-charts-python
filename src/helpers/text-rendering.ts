export function resolveTextColor(textColor: string, lineColor: string): string {
    return textColor || lineColor;
}

export function drawShapeText(
    ctx: CanvasRenderingContext2D,
    bmpX: number,
    bmpY: number,
    text: string,
    color: string,
    fontSizePx: number,
    hAlign: CanvasTextAlign,
    vAlign: CanvasTextBaseline,
): void {
    if (!text) return;

    ctx.save();
    ctx.font = `${fontSizePx}px -apple-system, BlinkMacSystemFont, sans-serif`;
    ctx.fillStyle = color;
    ctx.textAlign = hAlign;
    ctx.textBaseline = vAlign;
    ctx.fillText(text, bmpX, bmpY);
    ctx.restore();
}
