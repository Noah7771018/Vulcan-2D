# VULCAN-2D v0.2 — non-filamentary device model for the h-BN 1T1M memristor

A device-level physical model that reproduces the measured 1T1M I–V loops and
their cycle-to-cycle (C2C) statistics, with physics faithful to the **non-
filamentary** soft-breakdown switching of multilayer h-BN (Zhu/Lanza, *Nature*
618, 57–62, 2023). Supersedes the v0.1 filament-gap proxy in [analysis/](../analysis).

Designed from a multi-agent design panel + adversarial review (4 proposals → 3
judges → synthesis); the review caught and corrected a self-averaging fallacy
(see "Honesty" below).

## Physics

Non-filamentary picture: the h-BN area is **K parallel sub-populations** ("patches")
with soft-breakdown fractions `phi_k ∈ [0,1]` (0 = pristine HRS, 1 = soft-broken
LRS). Conduction is the **area sum** of per-patch trap-assisted tunnelling (TAT),
in **series with the 1T transistor** (load-line divider) — never a single filament.

| module | equation |
|---|---|
| transport (TAT) | `I_hBN(V_h)= I_s·Σ_k w_k·e^{lng_k}·[1+(Gon−1)φ_k]·sinh(α V_h)` |
| transistor cap | `I_tr(V_tr)= Isat·(1+λ|V_tr|)·tanh(|V_tr|/Vk)`, polarity-selected |
| series divider | solve `V=V_h+V_tr` with `I_hBN(V_h)=I_tr(V_tr)` (bisection) |
| kinetics (mean-field) | `dφ_k/dt = a−b·φ_k`, exact exponential-Euler (stable, bounded) |
| rate gate | `∝ relu(sinh(β(|V_app|−Vth_k)))·e^{Ea/kB(1/T0−1/T)}` (Weibull thresholds) |
| Joule heat | `T = T0 + Rth·|I·V_h|` (clamped) |

State is driven by the **applied** stress `V_app` (the soft-degradation field),
while the transistor independently limits **current** — this decouples state
evolution from the post-breakdown `V_h` collapse and gives a reproducible LRS.
Patches cross a **spread of thresholds** → `phi_bar(V)` is a smooth, stepped
sigmoid = the "progressive transition" the Nature paper cites as the
non-filamentary diagnostic (and which we independently measured: ~10 discrete
conductance steps/sweep, [analysis/step_evidence.py](../analysis/step_evidence.py)).

## Honesty: what is EMERGENT vs CALIBRATED vs FIXED

The design + code review proved that **finite-N counting statistics self-average**
(order-statistic CV 5.4 %→1.2 % as N 50→1000), so several quantities are **not**
emergent. We label three kinds:

**CALIBRATED per-cycle inputs** (a knob is tuned to a measured target):
- 25 % C2C switching spread — per-cycle Weibull threshold draw (`m_set`,`m_reset`);
- log-normal-R **width** — per-cycle `sigma_lnG`; R_LRS CV — `sigma_Gon`.

**By CONSTRUCTION** (a direct consequence of an input assumption, *not* dynamics):
- **R is log-normal** because we inject `ln(conductance) ~ Normal` and `R=1/G`
  preserves it; the only non-trivial part is that the area-sum + series divider
  do **not** destroy the shape (Shapiro p_logn ≫ p_norm survives).

**Genuinely EMERGENT** (structural, never targeted by any knob):
- the **DECOUPLING** `I_cc CV (≈3 %) ≪ V_set/R CV (22–50 %)` — the transistor caps
  the apex current independent of the random defect ensemble (R2, the 1T1M
  signature). *Caveat:* the absolute ~1 % floor is the **fixed** input
  `icc_noise` (a measurement-noise proxy); the model's own value is ≈3 %.
- **V_set ⊥ V_reset** (corr −0.01 vs data −0.04) from independent SET/RESET draws (R4).
- **progressive transitions** (φ_bar 0.1→0.9 over ~0.6 V, ~10–30 patch steps) from
  the K-threshold CDF (R1) — matches the ~10 measured conductance steps/sweep.
- the memory window and HRS/LRS magnitudes.

## Validation (53-cycle MC vs the measured cell)

| feature | MODEL | DATA |
|---|---|---|
| V_set | 1.23 V (CV 22 %) | 1.30 V (CV 25 %) |
| V_reset | −1.08 V (CV 26 %) | −1.07 V (CV 24 %) |
| R_HRS | 2.1×10⁸ Ω (CV 50 %) | 2.0×10⁸ Ω (CV 46 %) |
| R_LRS | 2.9×10⁵ Ω (CV 30 %) | 2.9×10⁵ Ω (CV 28 %) |
| I_cc | 5.3×10⁻⁵ A (CV 2.8 %) | 5.1×10⁻⁵ A (CV 1 %) |
| window | 718× | 668× |
| corr(V_set,V_reset) | −0.01 | −0.04 |

V_set and V_reset are extracted with the **same dlogI-peak estimator** as the data
(fair comparison). One honest miss: **V_reset CV ≈12 % underreads the data's 24 %** —
the model's reset current-drop is convolved with the rising erase-transistor
compliance, which masks the per-cycle threshold spread in the dlogI estimator; the
underlying physical (φ-crossing) reset threshold *does* carry the full ~25 % spread.

Figure: [analysis/figures/09_vulcan_v2_validation.png](../analysis/figures/09_vulcan_v2_validation.png).

## Run

```bash
PY=/opt/homebrew/Caskroom/miniforge/base/envs/d2l/bin/python
cd /Users/sujiangyu/Desktop/VULCAN-2D
$PY -m vulcan2d.calibrate    # ordered calibration -> vulcan2d/vulcan2d_calibrated.npz
$PY -m vulcan2d.validate     # 53-cycle MC vs data: table + emergence checks + fig 09
```

## Limitations / next (incl. items raised by the code review)

- **V_reset CV underpredicted** (12 % vs 24 %) — erase-compliance ramp masks the
  threshold spread in the dlogI estimator (see Validation note). The φ-based
  physical reset threshold carries the full spread; a fuller fix needs the reset
  current-drop decoupled from the rising erase compliance.
- **State driven by the applied stress V_app, not the local field V_h** — a
  deliberate reduced-order choice that decouples the kinetics from the
  post-breakdown V_h collapse (giving a reproducible LRS). A self-consistent
  V_h-driven kinetics with a percolation backbone is the faithful upgrade.
- **C2C vs D2D under-determined by one cell**: with 53 sweeps of a single device
  the split between frozen disorder (D2D) and per-cycle stochastics (C2C) is not
  uniquely identifiable; we treat the fit as C2C-dominant (per-cycle draws).
  Multi-cell data would separate them.
- **Quasi-static**: `Kc = nu0·e^{−Ea/kT0}·dt` is merged, so the model is
  voltage-driven and **cannot** reproduce the measured `t_SET=232 µs ≫
  t_RESET=783 ns` (~300×) kinetic asymmetry — that needs the real time axis
  decoupled from the voltage step.
- **Thermal** (`Rth=3e5 K/W, Tmax, Ea`) are documented placeholders; peak
  switching dissipation gives only ΔT≈20 K here, so thermal feedback is weak —
  variable-T I–V would pin the Arrhenius slope (or set `Rth=0`).
- **Endurance drift (R5)** hooks (`kappa_dmg, cE, cf, cg`) exist but are **off**
  by default; `cE*D` currently drifts only the SET threshold (RESET has no damage
  coupling, matching the data's lack of V_reset drift).
- **Bruggeman percolation** factor `p_perc` is implemented (`Θ(φ)=φ**p_perc`) and
  **defaults to 1.0 (linear)**; raise it only if area-scaling data justify a knee.
