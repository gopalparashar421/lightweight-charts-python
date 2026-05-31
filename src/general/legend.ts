import {
  AreaStyleOptions,
  BarStyleOptions,
  BaselineStyleOptions,
  CandlestickStyleOptions,
  HistogramStyleOptions,
  ISeriesApi,
  LastPriceAnimationMode,
  LineData,
  LineStyle,
  LineStyleOptions,
  LineType,
  Logical,
  MouseEventParams,
  PriceFormatBuiltIn,
  SeriesOptionsCommon,
  SeriesType,
} from "lightweight-charts";
import { Handler } from "./handler";

interface LineElement {
  name: string;
  div: HTMLDivElement;
  row: HTMLDivElement;
  toggle: HTMLDivElement;
  series: ISeriesApi<SeriesType>;
  solid: string;
}

type FieldType = "color" | "number" | "boolean" | "select" | "text";

interface SelectOption {
  value: number | string;
  label: string;
}

interface FieldDef {
  key: string;
  label: string;
  type: FieldType;
  min?: number;
  max?: number;
  step?: number;
  options?: SelectOption[];
}

interface FieldGroup {
  title: string;
  fields: FieldDef[];
}

export class Legend {
  private handler: Handler;
  private _paneIndex: number;
  private _anchored: boolean = false;
  public div: HTMLDivElement;
  public seriesContainer: HTMLDivElement;

  public ohlcEnabled: boolean = false;
  public percentEnabled: boolean = false;
  public linesEnabled: boolean = false;
  public colorBasedOnCandle: boolean = false;

  private text: HTMLSpanElement;
  private candle: HTMLDivElement;
  public _lines: LineElement[] = [];

  constructor(paneIndex: number, handler: Handler) {
    this.legendHandler = this.legendHandler.bind(this);

    this._paneIndex = paneIndex;
    this.handler = handler;

    this.div = document.createElement("div");
    this.div.classList.add("legend");
    this.div.style.display = "none";

    const seriesWrapper = document.createElement("div");
    seriesWrapper.style.display = "flex";
    seriesWrapper.style.flexDirection = "row";
    this.seriesContainer = document.createElement("div");
    this.seriesContainer.classList.add("series-container");

    this.text = document.createElement("span");
    this.text.style.lineHeight = "1.8";
    this.candle = document.createElement("div");

    seriesWrapper.appendChild(this.seriesContainer);
    this.div.appendChild(this.text);
    this.div.appendChild(this.candle);
    this.div.appendChild(seriesWrapper);

    // DOM anchoring is deferred to tryAnchorToPane() — the pane element
    // may not exist yet at construction time.
  }

  /**
   * Lazily anchors the legend div to the inner chart area div of its pane.
   * IPaneApi.getHTMLElement() returns a <tr>; the chart area is at
   * tr.children[1].children[0] (<td> → <div position:relative overflow:hidden>).
   * Safe to call repeatedly — no-ops once anchored.
   */
  tryAnchorToPane() {
    if (this._anchored) return;
    const panes = this.handler.chart.panes();
    if (this._paneIndex >= panes.length) return;
    const tr = panes[this._paneIndex].getHTMLElement();
    if (!tr) return;
    const td = tr.children[1] as HTMLElement | undefined;
    if (!td) return;
    const innerDiv = td.children[0] as HTMLDivElement | undefined;
    if (!innerDiv) return;
    innerDiv.appendChild(this.div);
    this._anchored = true;
  }

  toJSON() {
    // Exclude the chart attribute from serialization
    const { _lines, handler, ...serialized } = this;
    return serialized;
  }

  makeSeriesRow(name: string, series: ISeriesApi<SeriesType>) {
    this.tryAnchorToPane();
    const strokeColor = "#FFF";
    let openEye = `
    <path style="fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke:${strokeColor};stroke-opacity:1;stroke-miterlimit:4;" d="M 21.998437 12 C 21.998437 12 18.998437 18 12 18 C 5.001562 18 2.001562 12 2.001562 12 C 2.001562 12 5.001562 6 12 6 C 18.998437 6 21.998437 12 21.998437 12 Z M 21.998437 12 " transform="matrix(0.833333,0,0,0.833333,0,0)"/>
    <path style="fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke:${strokeColor};stroke-opacity:1;stroke-miterlimit:4;" d="M 15 12 C 15 13.654687 13.654687 15 12 15 C 10.345312 15 9 13.654687 9 12 C 9 10.345312 10.345312 9 12 9 C 13.654687 9 15 10.345312 15 12 Z M 15 12 " transform="matrix(0.833333,0,0,0.833333,0,0)"/>\`
    `;
    let closedEye = `
    <path style="fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke:${strokeColor};stroke-opacity:1;stroke-miterlimit:4;" d="M 20.001562 9 C 20.001562 9 19.678125 9.665625 18.998437 10.514062 M 12 14.001562 C 10.392187 14.001562 9.046875 13.589062 7.95 12.998437 M 12 14.001562 C 13.607812 14.001562 14.953125 13.589062 16.05 12.998437 M 12 14.001562 L 12 17.498437 M 3.998437 9 C 3.998437 9 4.354687 9.735937 5.104687 10.645312 M 7.95 12.998437 L 5.001562 15.998437 M 7.95 12.998437 C 6.689062 12.328125 5.751562 11.423437 5.104687 10.645312 M 16.05 12.998437 L 18.501562 15.998437 M 16.05 12.998437 C 17.38125 12.290625 18.351562 11.320312 18.998437 10.514062 M 5.104687 10.645312 L 2.001562 12 M 18.998437 10.514062 L 21.998437 12 " transform="matrix(0.833333,0,0,0.833333,0,0)"/>
    `;

    let row = document.createElement("div");
    row.style.display = "flex";
    row.style.alignItems = "center";
    let div = document.createElement("div");
    let toggle = document.createElement("div");
    toggle.classList.add("legend-toggle-switch");

    let svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("width", "22");
    svg.setAttribute("height", "16");

    let group = document.createElementNS("http://www.w3.org/2000/svg", "g");
    group.innerHTML = openEye;

    let on = true;
    toggle.addEventListener("click", () => {
      if (on) {
        on = false;
        group.innerHTML = closedEye;
        series.applyOptions({
          visible: false,
        });
      } else {
        on = true;
        series.applyOptions({
          visible: true,
        });
        group.innerHTML = openEye;
      }
    });

    svg.appendChild(group);
    toggle.appendChild(svg);

    // Gear / settings button
    const gearBtn = document.createElement("div");
    gearBtn.classList.add("legend-settings-btn");
    gearBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`;
    gearBtn.title = "Series settings";
    gearBtn.addEventListener("click", () => this.openSettingsModal(name, series));

    // Cross / remove button
    const crossBtn = document.createElement("div");
    crossBtn.classList.add("legend-cross-btn");
    crossBtn.innerHTML = "&#x2715;";
    crossBtn.title = "Remove series";
    crossBtn.addEventListener("click", () => {
      this.handler.chart.removeSeries(series);
      row.remove();
      const idx = this._lines.findIndex((l) => l.series === series);
      if (idx !== -1) this._lines.splice(idx, 1);
    });

    row.appendChild(div);
    row.appendChild(toggle);
    row.appendChild(gearBtn);
    row.appendChild(crossBtn);
    this.seriesContainer.appendChild(row);

    this._lines.push({
      name: name,
      div: div,
      row: row,
      toggle: toggle,
      series: series,
      solid: this.getSeriesDisplayColor(series),
    });
  }

  private getSeriesDisplayColor(series: ISeriesApi<SeriesType>): string {
    const t = series.seriesType();
    let raw: string;
    if (t === "Area") {
      raw = (series.options() as AreaStyleOptions & SeriesOptionsCommon).lineColor;
    } else if (t === "Baseline") {
      raw = (series.options() as BaselineStyleOptions & SeriesOptionsCommon).topLineColor;
    } else if (t === "Bar") {
      raw = (series.options() as BarStyleOptions & SeriesOptionsCommon).upColor;
    } else if (t === "Candlestick") {
      raw = (series.options() as CandlestickStyleOptions & SeriesOptionsCommon).upColor;
    } else if (t === "Line") {
      raw = (series.options() as LineStyleOptions & SeriesOptionsCommon).color;
    } else if (t === "Histogram") {
      raw = (series.options() as HistogramStyleOptions & SeriesOptionsCommon).color;
    } else {
      raw = (series.options() as SeriesOptionsCommon).baseLineColor;
    }
    raw = raw || "#2196f3";
    return raw.startsWith("rgba") ? raw.replace(/[^,]+(?=\))/, "1") : raw;
  }

  private colorToHex(color: string): string {
    if (!color) return "#000000";
    if (color.startsWith("#")) return color.length >= 7 ? color.slice(0, 7) : color;
    const m = color.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
    if (m) {
      return (
        "#" +
        parseInt(m[1]).toString(16).padStart(2, "0") +
        parseInt(m[2]).toString(16).padStart(2, "0") +
        parseInt(m[3]).toString(16).padStart(2, "0")
      );
    }
    return "#000000";
  }

  private getFieldGroups(series: ISeriesApi<SeriesType>): FieldGroup[] {
    const lineStyleOpts: SelectOption[] = [
      { value: LineStyle.Solid, label: "Solid" },
      { value: LineStyle.Dotted, label: "Dotted" },
      { value: LineStyle.Dashed, label: "Dashed" },
      { value: LineStyle.LargeDashed, label: "Large Dashed" },
      { value: LineStyle.SparseDotted, label: "Sparse Dotted" },
    ];
    const lineTypeOpts: SelectOption[] = [
      { value: LineType.Simple, label: "Simple" },
      { value: LineType.WithSteps, label: "With Steps" },
      { value: LineType.Curved, label: "Curved" },
    ];
    const animationOpts: SelectOption[] = [
      { value: LastPriceAnimationMode.Disabled, label: "Disabled" },
      { value: LastPriceAnimationMode.Continuous, label: "Continuous" },
      { value: LastPriceAnimationMode.OnDataUpdate, label: "On Data Update" },
    ];

    const commonFields: FieldDef[] = [
      { key: "title", label: "Label", type: "text" },
      { key: "lastValueVisible", label: "Last Value Label", type: "boolean" },
      { key: "priceLineVisible", label: "Price Line", type: "boolean" },
      { key: "priceLineColor", label: "Price Line Color", type: "color" },
      { key: "priceLineWidth", label: "Price Line Width", type: "number", min: 1, max: 4, step: 1 },
      { key: "priceLineStyle", label: "Price Line Style", type: "select", options: lineStyleOpts },
    ];

    const crosshairFields: FieldDef[] = [
      { key: "crosshairMarkerVisible", label: "Visible", type: "boolean" },
      { key: "crosshairMarkerRadius", label: "Radius (px)", type: "number", min: 1, max: 20, step: 1 },
      { key: "crosshairMarkerBorderColor", label: "Border Color", type: "color" },
      { key: "crosshairMarkerBackgroundColor", label: "BG Color", type: "color" },
      { key: "crosshairMarkerBorderWidth", label: "Border Width", type: "number", min: 1, max: 6, step: 1 },
    ];

    const t = series.seriesType();
    switch (t) {
      case "Line":
        return [
          {
            title: "Line",
            fields: [
              { key: "color", label: "Color", type: "color" },
              { key: "lineWidth", label: "Width", type: "number", min: 1, max: 4, step: 1 },
              { key: "lineStyle", label: "Style", type: "select", options: lineStyleOpts },
              { key: "lineType", label: "Type", type: "select", options: lineTypeOpts },
              { key: "lineVisible", label: "Line Visible", type: "boolean" },
              { key: "pointMarkersVisible", label: "Point Markers", type: "boolean" },
              { key: "pointMarkersRadius", label: "Marker Radius (px)", type: "number", min: 1, max: 20, step: 1 },
              { key: "lastPriceAnimation", label: "Price Animation", type: "select", options: animationOpts },
            ],
          },
          { title: "Crosshair Marker", fields: crosshairFields },
          { title: "General", fields: commonFields },
        ];

      case "Area":
        return [
          {
            title: "Area",
            fields: [
              { key: "lineColor", label: "Line Color", type: "color" },
              { key: "topColor", label: "Top Fill", type: "color" },
              { key: "bottomColor", label: "Bottom Fill", type: "color" },
              { key: "lineWidth", label: "Line Width", type: "number", min: 1, max: 4, step: 1 },
              { key: "lineStyle", label: "Line Style", type: "select", options: lineStyleOpts },
              { key: "lineType", label: "Line Type", type: "select", options: lineTypeOpts },
              { key: "lineVisible", label: "Line Visible", type: "boolean" },
              { key: "invertFilledArea", label: "Invert Fill", type: "boolean" },
              { key: "relativeGradient", label: "Relative Gradient", type: "boolean" },
              { key: "pointMarkersVisible", label: "Point Markers", type: "boolean" },
              { key: "pointMarkersRadius", label: "Marker Radius (px)", type: "number", min: 1, max: 20, step: 1 },
              { key: "lastPriceAnimation", label: "Price Animation", type: "select", options: animationOpts },
            ],
          },
          { title: "Crosshair Marker", fields: crosshairFields },
          { title: "General", fields: commonFields },
        ];

      case "Bar":
        return [
          {
            title: "Bar",
            fields: [
              { key: "upColor", label: "Up Color", type: "color" },
              { key: "downColor", label: "Down Color", type: "color" },
              { key: "openVisible", label: "Show Open Tick", type: "boolean" },
              { key: "thinBars", label: "Thin Bars", type: "boolean" },
            ],
          },
          { title: "General", fields: commonFields },
        ];

      case "Candlestick":
        return [
          {
            title: "Body",
            fields: [
              { key: "upColor", label: "Up Color", type: "color" },
              { key: "downColor", label: "Down Color", type: "color" },
            ],
          },
          {
            title: "Borders",
            fields: [
              { key: "borderVisible", label: "Visible", type: "boolean" },
              { key: "borderColor", label: "Color", type: "color" },
              { key: "borderUpColor", label: "Up Color", type: "color" },
              { key: "borderDownColor", label: "Down Color", type: "color" },
            ],
          },
          {
            title: "Wicks",
            fields: [
              { key: "wickVisible", label: "Visible", type: "boolean" },
              { key: "wickColor", label: "Color", type: "color" },
              { key: "wickUpColor", label: "Up Color", type: "color" },
              { key: "wickDownColor", label: "Down Color", type: "color" },
            ],
          },
          { title: "General", fields: commonFields },
        ];

      case "Histogram":
        return [
          {
            title: "Histogram",
            fields: [
              { key: "color", label: "Color", type: "color" },
              { key: "base", label: "Base Level", type: "number", step: 0.01 },
            ],
          },
          { title: "General", fields: commonFields },
        ];

      case "Baseline":
        return [
          {
            title: "Top Area",
            fields: [
              { key: "topLineColor", label: "Line Color", type: "color" },
              { key: "topFillColor1", label: "Fill Color 1", type: "color" },
              { key: "topFillColor2", label: "Fill Color 2", type: "color" },
            ],
          },
          {
            title: "Bottom Area",
            fields: [
              { key: "bottomLineColor", label: "Line Color", type: "color" },
              { key: "bottomFillColor1", label: "Fill Color 1", type: "color" },
              { key: "bottomFillColor2", label: "Fill Color 2", type: "color" },
            ],
          },
          {
            title: "Line",
            fields: [
              { key: "lineWidth", label: "Width", type: "number", min: 1, max: 4, step: 1 },
              { key: "lineStyle", label: "Style", type: "select", options: lineStyleOpts },
              { key: "lineType", label: "Type", type: "select", options: lineTypeOpts },
              { key: "lineVisible", label: "Visible", type: "boolean" },
              { key: "relativeGradient", label: "Relative Gradient", type: "boolean" },
              { key: "pointMarkersVisible", label: "Point Markers", type: "boolean" },
              { key: "pointMarkersRadius", label: "Marker Radius (px)", type: "number", min: 1, max: 20, step: 1 },
              { key: "lastPriceAnimation", label: "Price Animation", type: "select", options: animationOpts },
            ],
          },
          { title: "Crosshair Marker", fields: crosshairFields },
          { title: "General", fields: commonFields },
        ];

      default:
        return [{ title: "General", fields: commonFields }];
    }
  }

  private buildFieldRow(
    field: FieldDef,
    currentValue: unknown,
    onChange: (value: unknown) => void
  ): HTMLDivElement {
    const row = document.createElement("div");
    row.classList.add("legend-modal-field");

    const label = document.createElement("label");
    label.classList.add("legend-modal-field-label");
    label.textContent = field.label;

    let inputEl: HTMLElement;

    if (field.type === "color") {
      const colorInput = document.createElement("input");
      colorInput.type = "color";
      colorInput.value = this.colorToHex(typeof currentValue === "string" ? currentValue : "");
      colorInput.classList.add("legend-modal-color");
      colorInput.addEventListener("input", () => onChange(colorInput.value));
      inputEl = colorInput;
    } else if (field.type === "number") {
      const numInput = document.createElement("input");
      numInput.type = "number";
      if (field.min !== undefined) numInput.min = String(field.min);
      if (field.max !== undefined) numInput.max = String(field.max);
      if (field.step !== undefined) numInput.step = String(field.step);
      numInput.value = currentValue !== undefined ? String(currentValue) : "";
      numInput.classList.add("legend-modal-input");
      numInput.addEventListener("input", () => {
        const v = parseFloat(numInput.value);
        if (!isNaN(v)) onChange(v);
      });
      inputEl = numInput;
    } else if (field.type === "boolean") {
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = !!currentValue;
      checkbox.classList.add("legend-modal-checkbox");
      checkbox.addEventListener("change", () => onChange(checkbox.checked));
      inputEl = checkbox;
    } else if (field.type === "select") {
      const select = document.createElement("select");
      select.classList.add("legend-modal-input", "legend-modal-select");
      for (const opt of field.options ?? []) {
        const option = document.createElement("option");
        option.value = String(opt.value);
        option.textContent = opt.label;
        if (String(currentValue) === String(opt.value)) option.selected = true;
        select.appendChild(option);
      }
      select.addEventListener("change", () => onChange(Number(select.value)));
      inputEl = select;
    } else {
      const textInput = document.createElement("input");
      textInput.type = "text";
      textInput.value = String(currentValue ?? "");
      textInput.classList.add("legend-modal-input");
      textInput.addEventListener("input", () => onChange(textInput.value));
      inputEl = textInput;
    }

    row.appendChild(label);
    row.appendChild(inputEl);
    return row;
  }

  private openSettingsModal(name: string, series: ISeriesApi<SeriesType>) {
    const backdrop = document.createElement("div");
    backdrop.classList.add("legend-modal-backdrop");
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.remove();
    });

    const modal = document.createElement("div");
    modal.classList.add("legend-modal");
    modal.addEventListener("click", (e) => e.stopPropagation());

    // Header
    const header = document.createElement("div");
    header.classList.add("legend-modal-header");

    const titleEl = document.createElement("span");
    titleEl.classList.add("legend-modal-title");
    titleEl.textContent = `${name} \u00b7 ${series.seriesType()}`;

    const closeBtn = document.createElement("button");
    closeBtn.classList.add("legend-modal-close");
    closeBtn.innerHTML = "&#x2715;";
    closeBtn.title = "Close";
    closeBtn.addEventListener("click", () => backdrop.remove());

    header.appendChild(titleEl);
    header.appendChild(closeBtn);

    // Body
    const body = document.createElement("div");
    body.classList.add("legend-modal-body");

    const groups = this.getFieldGroups(series);
    const currentOpts = series.options() as SeriesOptionsCommon & Record<string, unknown>;

    for (const group of groups) {
      const section = document.createElement("div");
      section.classList.add("legend-modal-section");

      const sectionTitle = document.createElement("div");
      sectionTitle.classList.add("legend-modal-section-title");
      sectionTitle.textContent = group.title;
      section.appendChild(sectionTitle);

      for (const field of group.fields) {
        const fieldRow = this.buildFieldRow(field, currentOpts[field.key], (val) => {
          series.applyOptions({ [field.key]: val } as any);
          // Keep legend color swatch in sync
          const entry = this._lines.find((l) => l.series === series);
          if (entry) entry.solid = this.getSeriesDisplayColor(series);
        });
        section.appendChild(fieldRow);
      }

      body.appendChild(section);
    }

    modal.appendChild(header);
    modal.appendChild(body);
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
  }

  legendItemFormat(num: number, decimal: number) {
    return num.toFixed(decimal).toString().padStart(8, " ");
  }

  shorthandFormat(num: number) {
    const absNum = Math.abs(num);
    if (absNum >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (absNum >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toString().padStart(8, " ");
  }

  legendHandler(param: MouseEventParams, usingPoint = false) {
    this.tryAnchorToPane();
    if (!this.ohlcEnabled && !this.linesEnabled && !this.percentEnabled) return;

    // OHLC / percent / volume only belong on the main pane (index 0) because
    // they read from handler.series which is always the pane-0 candlestick.
    const isMainPane = this._paneIndex === 0;

    if (!param.time) {
      if (isMainPane) {
        const options: any = this.handler.series.options();
        this.candle.style.color = "transparent";
        this.candle.innerHTML = this.candle.innerHTML
          .replace(options["upColor"], "")
          .replace(options["downColor"], "");
      }
      if (!this.linesEnabled) return;
    }

    let data: any;
    let logical: Logical | null = null;

    if (isMainPane && param.time) {
      const options: any = this.handler.series.options();
      if (usingPoint) {
        const timeScale = this.handler.chart.timeScale();
        let coordinate = timeScale.timeToCoordinate(param.time);
        if (coordinate)
          logical = timeScale.coordinateToLogical(coordinate.valueOf());
        if (logical) data = this.handler.series.dataByIndex(logical.valueOf());
      } else {
        data = param.seriesData.get(this.handler.series);
      }

      this.candle.style.color = "";
      let str = '<span style="line-height: 1.8;">';
      if (data) {
        if (this.ohlcEnabled) {
          str += `O ${this.legendItemFormat(data.open, this.handler.precision)} `;
          str += `| H ${this.legendItemFormat(data.high, this.handler.precision)} `;
          str += `| L ${this.legendItemFormat(data.low, this.handler.precision)} `;
          str += `| C ${this.legendItemFormat(data.close, this.handler.precision)} `;
        }

        if (this.percentEnabled) {
          let percentMove = ((data.close - data.open) / data.open) * 100;
          let color = percentMove > 0 ? options["upColor"] : options["downColor"];
          let percentStr = `${percentMove >= 0 ? "+" : ""}${percentMove.toFixed(2)} %`;
          if (this.colorBasedOnCandle) {
            str += `| <span style="color: ${color};">${percentStr}</span>`;
          } else {
            str += "| " + percentStr;
          }
        }

        if (this.handler.volumeSeries) {
          let volumeData: any;
          if (logical) {
            volumeData = this.handler.volumeSeries.dataByIndex(logical);
          } else {
            volumeData = param.seriesData.get(this.handler.volumeSeries);
          }
          if (volumeData) {
            str += this.ohlcEnabled
              ? `<br>V ${this.shorthandFormat(volumeData.value)}`
              : "";
          }
        }
      }
      this.candle.innerHTML = str + "</span>";
    }

    this._lines.forEach((e) => {
      if (!this.linesEnabled) {
        e.row.style.display = "none";
        return;
      }
      e.row.style.display = "flex";

      let data;
      if (usingPoint && logical) {
        data = e.series.dataByIndex(logical) as LineData;
      } else {
        data = param.seriesData.get(e.series) as LineData;
      }
      if (!data?.value) return;
      let price;
      if (e.series.seriesType() == "Histogram") {
        price = this.shorthandFormat(data.value);
      } else {
        const format = e.series.options().priceFormat as PriceFormatBuiltIn;
        price = this.legendItemFormat(data.value, format.precision); // couldn't this just be line.options().precision?
      }
      e.div.innerHTML = `<span style="color: ${e.solid};">▨</span>    ${e.name} : ${price}`;
    });
  }
}
