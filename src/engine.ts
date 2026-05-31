// ============================================================================
//  Engine client — talks to the Python VULCAN-2D model server (vulcan2d.serve).
//  The validated physics lives in Python; the UI fetches simulated I-V loops,
//  the measured-data overlay, the phi_bar trajectory, and summary features.
// ============================================================================

export interface Loop {
  V: number[];
  med: number[];
  lo: number[];
  hi: number[];
}
export interface Stat {
  mean: number;
  cv: number;
}
export interface Features {
  Vset: Stat;
  Vreset: Stat;
  R_HRS: Stat;
  R_LRS: Stat;
  Icc: Stat;
  window: number;
  phi_final: number;
}
export interface Targets {
  Vset: number; Vset_cv: number;
  Vreset: number; Vreset_cv: number;
  R_HRS: number; R_LRS: number; Icc: number; window: number;
}
export interface SimResult {
  setLoop: Loop;
  resetLoop: Loop;
  measuredSet: Loop;
  measuredReset: Loop;
  phiBar: { V: number[]; phi: number[] };
  features: Features;
  targets: Targets;
  K: number;
  ncycles: number;
}

export interface SimParams {
  icc_ua?: number;  // compliance current target [µA]
  K?: number;       // number of areal sub-populations (patches)
  sigma?: number;   // variability knob (UI default 0.45)
  vset?: number;    // mean SET threshold [V]
  ncycles?: number; // Monte Carlo cycles
  seed?: number;    // RNG seed
}

const BASE = (import.meta as any).env?.VITE_ENGINE_URL || 'http://127.0.0.1:8000';

export async function simulate(p: SimParams): Promise<SimResult> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(p)) {
    if (v !== undefined && v !== null) q.set(k, String(v));
  }
  const r = await fetch(`${BASE}/simulate?${q.toString()}`);
  if (!r.ok) throw new Error(`engine ${r.status}`);
  return r.json() as Promise<SimResult>;
}

export async function ping(): Promise<boolean> {
  try {
    const r = await fetch(`${BASE}/health`);
    return r.ok;
  } catch {
    return false;
  }
}
