import {
  ColorType,
  CrosshairMode,
  DeepPartial,
  AreaStyleOptions,
  HistogramStyleOptions,
  IChartApi,
  ISeriesApi,
  LineStyleOptions,
  SeriesOptionsCommon,
  SeriesType,
  createChart,
  AreaSeries,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createTextWatermark,
  createSeriesMarkers,
} from "lightweight-charts";

import { GlobalParams, globalParamInit } from "./global-params";
import { Legend } from "./legend";
import { ToolBox } from "./toolbox";
import { TopBar } from "./topbar";

export interface Scale {
  width: number;
  height: number;
}

globalParamInit();
declare const window: GlobalParams;

export class Handler {
  public id: string;
  public commandFunctions: Function[] = [];

  public wrapper: HTMLDivElement;
  public div: HTMLDivElement;

  public chart: IChartApi;
  public scale: Scale;
  public precision: number = 2;

  public series: ISeriesApi<SeriesType>;
  public volumeSeries: ISeriesApi<SeriesType>;

  /** Per-pane legend instances, keyed by pane index. */
  public legends: Map<number, Legend> = new Map();
  /** Backward-compat accessor — always returns the pane-0 legend. */
  public get legend(): Legend { return this.legends.get(0)!; }
  private _topBar: TopBar | undefined;
  public toolBox: ToolBox | undefined;
  public spinner: HTMLDivElement | undefined;

  public _seriesList: ISeriesApi<SeriesType>[] = [];
  public watermark: any;
  public seriesMarkers: any;

  // TODO find a better solution rather than the 'position' parameter
  constructor(
    chartId: string,
    innerWidth: number,
    innerHeight: number,
    position: string,
    autoSize: boolean
  ) {
    this.reSize = this.reSize.bind(this);

    this.id = chartId;
    this.scale = {
      width: innerWidth,
      height: innerHeight,
    };

    this.wrapper = document.createElement("div");
    this.wrapper.classList.add("handler");
    this.wrapper.style.float = position;

    this.div = document.createElement("div");
    this.div.style.position = "relative";

    this.wrapper.appendChild(this.div);
    window.containerDiv.append(this.wrapper);

    this.chart = this._createChart();
    this.series = this.createCandlestickSeries(0);
    this.volumeSeries = this.createVolumeSeries(0);
    this.seriesMarkers = createSeriesMarkers(this.series, []);

    // Create pane-0 legend; DOM anchoring deferred until pane element is ready.
    this.legends.set(0, new Legend(0, this));

    // Single crosshair subscription — dispatches to all per-pane legends.
    this.chart.subscribeCrosshairMove((param) => {
      this.legends.forEach((leg) => leg.legendHandler(param));
    });

    document.addEventListener("keydown", (event) => {
      for (let i = 0; i < this.commandFunctions.length; i++) {
        if (this.commandFunctions[i](event)) break;
      }
    });
    window.handlerInFocus = this.id;
    this.wrapper.addEventListener(
      "mouseover",
      () => (window.handlerInFocus = this.id)
    );

    this.reSize();
    if (!autoSize) return;
    window.addEventListener("resize", () => this.reSize());
  }

  reSize() {
    let topBarOffset =
      this.scale.height !== 0 ? this._topBar?._div.offsetHeight || 0 : 0;
    this.chart.resize(
      window.innerWidth * this.scale.width,
      window.innerHeight * this.scale.height - topBarOffset
    );
    this.wrapper.style.width = `${100 * this.scale.width}%`;
    this.wrapper.style.height = `${100 * this.scale.height}%`;

    // TODO definitely a better way to do this
    if (this.scale.height === 0 || this.scale.width === 0) {
      // if (this.legend.div.style.display == 'flex') this.legend.div.style.display = 'none'
      if (this.toolBox) {
        this.toolBox.div.style.display = "none";
      }
    } else {
      // this.legend.div.style.display = 'flex'
      if (this.toolBox) {
        this.toolBox.div.style.display = "flex";
      }
    }
  }

  private _createChart() {
    return createChart(this.div, {
      width: window.innerWidth * this.scale.width,
      height: window.innerHeight * this.scale.height,
      layout: {
        textColor: window.pane.color,
        background: {
          color: "#000000",
          type: ColorType.Solid,
        },
        fontSize: 12,
      },
      rightPriceScale: {
        scaleMargins: { top: 0.3, bottom: 0.25 },
      },
      timeScale: { timeVisible: true, secondsVisible: false },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          labelBackgroundColor: "rgb(46, 46, 46)",
        },
        horzLine: {
          labelBackgroundColor: "rgb(55, 55, 55)",
        },
      },
      grid: {
        vertLines: { color: "rgba(29, 30, 38, 5)" },
        horzLines: { color: "rgba(29, 30, 58, 5)" },
      },
      handleScroll: { vertTouchDrag: true },
    });
  }

  createCandlestickSeries(paneIndex?: number) {
    const up = "rgba(39, 157, 130, 100)";
    const down = "rgba(200, 97, 100, 100)";
    const candleSeries = this.chart.addSeries(
      CandlestickSeries,
      {
        upColor: up,
        borderUpColor: up,
        wickUpColor: up,
        downColor: down,
        borderDownColor: down,
        wickDownColor: down,
      },
      paneIndex
    );
    candleSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.2, bottom: 0.2 },
    });
    return candleSeries;
  }

  createVolumeSeries(paneIndex?: number) {
    const volumeSeries = this.chart.addSeries(
      HistogramSeries,
      {
        color: "#26a69a",
        priceFormat: { type: "volume" },
        priceScaleId: "volume_scale",
      },
      paneIndex
    );
    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    return volumeSeries;
  }

  /**
   * Returns the Legend for the given pane, creating one lazily if it does not
   * yet exist. This is the preferred accessor from both internal series-creation
   * methods and the Python `getOrCreateLegend(idx)` bridge.
   */
  getOrCreateLegend(paneIndex: number): Legend {
    if (!this.legends.has(paneIndex)) {
      this.legends.set(paneIndex, new Legend(paneIndex, this));
    }
    return this.legends.get(paneIndex)!;
  }

  createLineSeries(
    name: string,
    options: DeepPartial<LineStyleOptions & SeriesOptionsCommon>,
    paneIndex?: number
  ) {
    const line = this.chart.addSeries(LineSeries, { ...options }, paneIndex);
    this._seriesList.push(line);
    this.getOrCreateLegend(paneIndex ?? 0).makeSeriesRow(name, line);

    return {
      name: name,
      series: line,
    };
  }

  createHistogramSeries(
    name: string,
    options: DeepPartial<HistogramStyleOptions & SeriesOptionsCommon>,
    paneIndex?: number
  ) {
    const line = this.chart.addSeries(
      HistogramSeries,
      { ...options },
      paneIndex
    );
    this._seriesList.push(line);
    this.getOrCreateLegend(paneIndex ?? 0).makeSeriesRow(name, line);
    return {
      name: name,
      series: line,
    };
  }

  createAreaSeries(
    name: string,
    options: DeepPartial<AreaStyleOptions & SeriesOptionsCommon>,
    paneIndex?: number
  ) {
    const area = this.chart.addSeries(AreaSeries, { ...options }, paneIndex);
    this._seriesList.push(area);
    this.getOrCreateLegend(paneIndex ?? 0).makeSeriesRow(name, area);
    return {
      name: name,
      series: area,
    };
  }

  createToolBox() {
    this.toolBox = new ToolBox(
      this.id,
      this.chart,
      this.series,
      this.commandFunctions
    );
    this.div.appendChild(this.toolBox.div);
  }

  createTopBar() {
    this._topBar = new TopBar(this);
    this.wrapper.prepend(this._topBar._div);
    return this._topBar;
  }

  toJSON() {
    // Exclude the chart attribute from serialization
    const { chart, ...serialized } = this;
    return serialized;
  }

  public static makeSearchBox(chart: Handler) {
    const searchWindow = document.createElement("div");
    searchWindow.classList.add("searchbox");
    searchWindow.style.display = "none";

    const magnifyingGlass = document.createElement("div");
    magnifyingGlass.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="24px" height="24px" viewBox="0 0 24 24" version="1.1"><path style="fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke:lightgray;stroke-opacity:1;stroke-miterlimit:4;" d="M 15 15 L 21 21 M 10 17 C 6.132812 17 3 13.867188 3 10 C 3 6.132812 6.132812 3 10 3 C 13.867188 3 17 6.132812 17 10 C 17 13.867188 13.867188 17 10 17 Z M 10 17 "/></svg>`;

    const sBox = document.createElement("input");
    sBox.type = "text";

    searchWindow.appendChild(magnifyingGlass);
    searchWindow.appendChild(sBox);
    chart.div.appendChild(searchWindow);

    chart.commandFunctions.push((event: KeyboardEvent) => {
      if (window.handlerInFocus !== chart.id || window.textBoxFocused)
        return false;
      if (searchWindow.style.display === "none") {
        if (/^[a-zA-Z0-9]$/.test(event.key)) {
          searchWindow.style.display = "flex";
          sBox.focus();
          return true;
        } else return false;
      } else if (event.key === "Enter" || event.key === "Escape") {
        if (event.key === "Enter")
          window.callbackFunction(`search${chart.id}_~_${sBox.value}`);
        searchWindow.style.display = "none";
        sBox.value = "";
        return true;
      } else return false;
    });
    sBox.addEventListener(
      "input",
      () => (sBox.value = sBox.value.toUpperCase())
    );
    return {
      window: searchWindow,
      box: sBox,
    };
  }

  public static makeSpinner(chart: Handler) {
    chart.spinner = document.createElement("div");
    chart.spinner.classList.add("spinner");
    chart.wrapper.appendChild(chart.spinner);

    // TODO below can be css (animate)
    let rotation = 0;
    const speed = 10;
    function animateSpinner() {
      if (!chart.spinner) return;
      rotation += speed;
      chart.spinner.style.transform = `translate(-50%, -50%) rotate(${rotation}deg)`;
      requestAnimationFrame(animateSpinner);
    }
    animateSpinner();
  }

  private static readonly _styleMap = {
    "--bg-color": "backgroundColor",
    "--hover-bg-color": "hoverBackgroundColor",
    "--click-bg-color": "clickBackgroundColor",
    "--active-bg-color": "activeBackgroundColor",
    "--muted-bg-color": "mutedBackgroundColor",
    "--border-color": "borderColor",
    "--color": "color",
    "--active-color": "activeColor",
  };
  public static setRootStyles(styles: any) {
    const rootStyle = document.documentElement.style;
    for (const [property, valueKey] of Object.entries(this._styleMap)) {
      rootStyle.setProperty(property, styles[valueKey]);
    }
  }

  createWatermark(text: string, fontSize: number, color: string) {
    if (!this.watermark) {
      this.watermark = createTextWatermark(this.chart.panes()[0], {
        horzAlign: 'center',
        vertAlign: 'center',
        lines: [{
          text: text,
          color: color,
          fontSize: fontSize,
        }],
      });

      return;
    }

    this.watermark.applyOptions({
      lines: [{
        text: text,
        color: color,
        fontSize: fontSize,
      }]
    });
  }
}
