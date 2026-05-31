// ============================================================================
//  I–V plot (Canvas 2D) — model vs measured, simple & legible.
//
//  Draws the device's SET (0→+5→0) and RESET (0→−1.7→0) median loops on a quiet
//  log|I|–V grid, with the MEASURED median loops underneath in grey. The clean
//  overlay is the "experiment ↔ simulation" closed loop. A soft 10–90% band
//  shows variability without spaghetti.
// ============================================================================

import type { Loop } from '../engine';

const LOG_MIN = -11; // 1e-11 A
const LOG_MAX = -3; //  1e-3 A
const I_FLOOR = 1e-12;

export interface SeriesStyle {
  line: string;
  band: string;
  glow: string;
  width: number;
  label: string;
}

export const STYLE_MODEL: SeriesStyle = {
  line: '#ff9a3c',
  band: 'rgba(255,154,60,0.12)',
  glow: 'rgba(255,154,60,0.55)',
  width: 2.8,
  label: 'VULCAN-2D model',
};
export const STYLE_DATA: SeriesStyle = {
  line: '#8b93a3',
  band: 'rgba(139,147,163,0.10)',
  glow: 'rgba(0,0,0,0)',
  width: 1.6,
  label: 'measured cell',
};

export interface PlotSeries {
  set: Loop;
  reset: Loop;
  style: SeriesStyle;
}

export class IVPlot {
  private ctx: CanvasRenderingContext2D;
  private canvas: HTMLCanvasElement;
  private Vmin: number;
  private Vmax: number;
  private series: PlotSeries[] = [];
  private w = 0;
  private h = 0;
  private dpr = 1;

  constructor(canvas: HTMLCanvasElement, Vmin = -2, Vmax = 5) {
    this.canvas = canvas;
    this.Vmin = Vmin;
    this.Vmax = Vmax;
    const ctx = canvas.getContext('2d');
    if (!ctx) throw new Error('2D context unavailable');
    this.ctx = ctx;
    this.resize();
  }

  /** Series are drawn in order, so pass measured (grey) before model (amber). */
  setSeries(series: PlotSeries[]) {
    this.series = series;
    this.draw();
  }

  resize() {
    this.dpr = Math.min(window.devicePixelRatio || 1, 2);
    this.w = this.canvas.clientWidth;
    this.h = this.canvas.clientHeight;
    this.canvas.width = Math.round(this.w * this.dpr);
    this.canvas.height = Math.round(this.h * this.dpr);
    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    this.draw();
  }

  private get pad() {
    return { l: 82, r: 34, t: 40, b: 56 };
  }
  private px(V: number): number {
    const { l, r } = this.pad;
    const t = (V - this.Vmin) / (this.Vmax - this.Vmin);
    return l + t * (this.w - l - r);
  }
  private py(I: number): number {
    const { t, b } = this.pad;
    const mag = Math.max(I_FLOOR, Math.abs(I));
    const f = (Math.log10(mag) - LOG_MIN) / (LOG_MAX - LOG_MIN);
    return this.h - b - f * (this.h - t - b);
  }

  draw() {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.w, this.h);
    this.drawGrid();
    for (const s of this.series) {
      this.drawBand(s.set, s.style);
      this.drawBand(s.reset, s.style);
    }
    for (const s of this.series) {
      this.drawLoop(s.set, s.style);
      this.drawLoop(s.reset, s.style);
    }
    this.drawLegend();
  }

  private drawGrid() {
    const ctx = this.ctx;
    const { l, r, t, b } = this.pad;
    const x0 = l;
    const x1 = this.w - r;
    const y0 = t;
    const y1 = this.h - b;

    const g = ctx.createLinearGradient(0, y0, 0, y1);
    g.addColorStop(0, 'rgba(255,255,255,0.015)');
    g.addColorStop(1, 'rgba(0,0,0,0.10)');
    ctx.fillStyle = g;
    ctx.fillRect(x0, y0, x1 - x0, y1 - y0);

    ctx.lineWidth = 1;
    ctx.font = '14px ui-monospace, "JetBrains Mono", monospace';
    ctx.fillStyle = '#8a8f9c';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'right';
    for (let dec = LOG_MIN; dec <= LOG_MAX; dec += 2) {
      const y = this.py(Math.pow(10, dec));
      ctx.strokeStyle = 'rgba(255,255,255,0.055)';
      ctx.beginPath();
      ctx.moveTo(x0, y);
      ctx.lineTo(x1, y);
      ctx.stroke();
      ctx.fillText(`10${sup(dec)}`, x0 - 10, y);
    }
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let v = Math.ceil(this.Vmin); v <= Math.floor(this.Vmax); v++) {
      const x = this.px(v);
      ctx.strokeStyle = v === 0 ? 'rgba(255,255,255,0.16)' : 'rgba(255,255,255,0.055)';
      ctx.beginPath();
      ctx.moveTo(x, y0);
      ctx.lineTo(x, y1);
      ctx.stroke();
      ctx.fillText(`${v}`, x, y1 + 9);
    }

    ctx.fillStyle = '#a2a8b4';
    ctx.font = '14px ui-sans-serif, system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Voltage  (V)', (x0 + x1) / 2, this.h - 16);
    ctx.save();
    ctx.translate(20, (y0 + y1) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Current  |I|  (A)', 0, 0);
    ctx.restore();
  }

  private drawBand(loop: Loop, style: SeriesStyle) {
    const { V, lo, hi } = loop;
    if (!V || V.length < 2) return;
    const ctx = this.ctx;
    const p = new Path2D();
    for (let i = 0; i < V.length; i++) {
      const x = this.px(V[i]);
      const y = this.py(hi[i]);
      if (i === 0) p.moveTo(x, y);
      else p.lineTo(x, y);
    }
    for (let i = V.length - 1; i >= 0; i--) p.lineTo(this.px(V[i]), this.py(lo[i]));
    p.closePath();
    ctx.fillStyle = style.band;
    ctx.fill(p);
  }

  private drawLoop(loop: Loop, style: SeriesStyle) {
    const { V, med } = loop;
    if (!V || V.length < 2) return;
    const ctx = this.ctx;
    const path = new Path2D();
    for (let i = 0; i < V.length; i++) {
      const x = this.px(V[i]);
      const y = this.py(med[i]);
      if (i === 0) path.moveTo(x, y);
      else path.lineTo(x, y);
    }
    ctx.save();
    ctx.lineJoin = 'round';
    ctx.lineCap = 'round';
    if (style.glow !== 'rgba(0,0,0,0)') {
      ctx.shadowColor = style.glow;
      ctx.shadowBlur = 12;
    }
    ctx.strokeStyle = style.line;
    ctx.lineWidth = style.width;
    ctx.stroke(path);
    ctx.restore();
  }

  private drawLegend() {
    if (!this.series.length) return;
    const ctx = this.ctx;
    const { l, t } = this.pad;
    let x = l + 14;
    const y = t + 14;
    ctx.font = '15px ui-sans-serif, system-ui, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    for (const s of this.series) {
      ctx.fillStyle = s.style.line;
      ctx.fillRect(x, y - 2, 20, 4);
      ctx.fillStyle = '#d6dae2';
      ctx.fillText(s.style.label, x + 28, y);
      x += 28 + ctx.measureText(s.style.label).width + 28;
    }
  }
}

function sup(n: number): string {
  const map: Record<string, string> = {
    '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
  };
  return String(n).split('').map((c) => map[c] ?? c).join('');
}
