// ============================================================================
//  Forge color language.
//   HOT  (forge blackbody ramp ember→white): 1T1M band, filament, heat field.
//   COLD (electric cyan→blue): the uncontained, chaotic bare-1R cloud.
//  Mapping current magnitude / temperature onto one intuitive "how hot / how
//  conductive" scale is the project's visual through-line.
// ============================================================================

import { Color } from 'three';

/** Forge blackbody ramp: t∈[0,1] → deep-red → ember → forge-yellow → white-hot. */
export function forgeRamp(t: number): Color {
  const x = Math.max(0, Math.min(1, t));
  // piecewise stops in linear RGB-ish space
  const stops: [number, [number, number, number]][] = [
    [0.0, [0.18, 0.02, 0.01]],
    [0.35, [1.0, 0.28, 0.0]],
    [0.7, [1.0, 0.74, 0.18]],
    [1.0, [1.0, 0.98, 0.9]],
  ];
  for (let i = 0; i < stops.length - 1; i++) {
    const [t0, c0] = stops[i];
    const [t1, c1] = stops[i + 1];
    if (x <= t1) {
      const f = (x - t0) / (t1 - t0);
      return new Color(
        c0[0] + (c1[0] - c0[0]) * f,
        c0[1] + (c1[1] - c0[1]) * f,
        c0[2] + (c1[2] - c0[2]) * f
      );
    }
  }
  return new Color(1, 0.98, 0.9);
}

/** Cold electric ramp for the bare-1R cloud: t∈[0,1] → deep-blue → cyan. */
export function coldRamp(t: number): Color {
  const x = Math.max(0, Math.min(1, t));
  const lo = new Color(0.06, 0.18, 0.5);
  const hi = new Color(0.21, 0.84, 1.0);
  return lo.clone().lerp(hi, x);
}

export const COLORS = {
  obsidian: 0x0a0a0d,
  ember: 0xff6a00,
  forgeYellow: 0xffd23f,
  whiteHot: 0xfffbe6,
  coldCyan: 0x36d6ff,
  coldBlue: 0x2b6cff,
  grid: 0x2a2530,
  axis: 0x4a4350,
} as const;
