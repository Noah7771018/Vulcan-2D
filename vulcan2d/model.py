"""VULCAN-2D v0.2 — non-filamentary (mean-field soft-breakdown) dynamic device
model for the h-BN 1T1M memristor.  Designed from a multi-agent design panel +
adversarial review (see analysis/ for data, README_v0.2.md for physics).

Core ideas (NON-filamentary, faithful to Zhu/Lanza Nature 2023):
  * The h-BN slab is K parallel areal sub-populations ("patches"); each patch k
    has a soft-breakdown fraction phi_k in [0,1] (0=pristine HRS, 1=soft-broken
    LRS).  Conduction = AREA SUM of per-patch trap-assisted-tunnelling (TAT),
    NOT a single filament.  phi_bar = sum_k w_k phi_k.
  * Switching = progressive soft breakdown: patches cross a spread of thresholds
    -> phi_bar(V) is a smooth sigmoid (the "progressive transition" the paper
    cites as the non-filamentary diagnostic).
  * A series MOSFET (load-line divider) caps the current -> I_cc is set by the
    transistor alone, structurally decoupled from the defect ensemble.

HONESTY (verified by the design + code review). Three kinds of quantities:

  CALIBRATED per-cycle inputs (NOT emergent; finite-N counting self-averages to
  ~1-5% CV so it cannot make these):
    - per-cycle Weibull threshold draw  -> V_set/V_reset spread (CV~25%);
    - per-cycle log-conductance residual sigma_lnG -> R spread WIDTH;
    - per-cycle LRS conductance spread sigma_Gon -> R_LRS CV.
  By CONSTRUCTION (direct consequence of an input assumption, not dynamics):
    - R is LOG-NORMAL because ln(conductance)~Normal is injected and survives the
      reciprocal series divider (R=1/G). The non-trivial part is only that the
      area-sum + divider do NOT destroy the shape.
  GENUINELY EMERGENT (structural, never targeted by any calibration knob):
    - the DECOUPLING I_cc CV (~3%) << V_set/R CV (22-50%): the transistor caps the
      apex current independent of the random defect ensemble.  NB the absolute
      ~1% floor is the FIXED input icc_noise (a measurement-noise proxy); the
      model's own value is ~3% (decoupling + divider sensitivity), not 1%.
    - V_set/V_reset INDEPENDENCE (corr~0): disjoint SET/RESET random draws.
    - PROGRESSIVE transitions: K patches cross a spread of thresholds.
    - the memory window and HRS/LRS magnitudes.
"""
from dataclasses import dataclass, field, asdict
import numpy as np

KB = 8.617333e-5  # eV/K


# ----------------------------------------------------------------------------
@dataclass
class Params:
    # --- transport: h-BN TAT (FIXED from HRS sinh fit, R2_log=0.998) ---
    I_s: float = 6.224e-10     # pristine ensemble TAT scale [A]; R_HRS0=1/(I_s*alpha)
    alpha: float = 6.747       # sinh field coefficient [1/V]  (FIXED)
    K: int = 10                # number of areal sub-populations (data: ~10 steps/sweep)
    Gon: float = 6.0e2         # full-LRS per-patch conductance lift (HRS->LRS swing)
    phi_floor: float = 1.0e-5  # residual breakdown fraction in HRS (must be << 1/Gon)
    Vclip: float = 5.8         # clip |V_h| in sinh(alpha*V_h) to avoid overflow
    p_perc: float = 1.0        # Bruggeman/percolation exponent: Theta(phi)=phi**p_perc
                               #   (1.0 = linear default; >1 sharpens the LRS knee)

    # --- transistor (SERIES-DIVIDER set; hits I_cc=51uA AND R_LRS@0.2V) ---
    Isat_set: float = 4.30e-7  # raised so apex I_cc=51uA after h-BN takes ~0.7V
    Vk_set: float = 0.45       # lowered from 0.759 so R_tr@0.2V < R_LRS target,
    lam_set: float = 27.4      #   letting the h-BN LRS series term carry R_LRS C2C
    Isat_reset: float = 29.4e-9
    Vk_reset: float = 0.355
    lam_reset: float = 119.2

    # --- kinetics (per-step effective rate constants Kc = nu0*exp(-Ea/kT0)*dt) ---
    Kc_set: float = 2.0        # SET generation rate constant (sharp per-patch;
    Kc_reset: float = 2.0      #   progressiveness comes from threshold spread)
    beta_set: float = 4.0      # field acceleration in SET gate [1/V]
    beta_reset: float = 5.0    # field acceleration in RESET gate [1/V]
    Ea_set: float = 1.00       # SET activation energy [eV] (thermal accel only)
    Ea_reset: float = 0.92     # RESET activation energy [eV]
    sigma_theta: float = 0.16  # frozen per-patch threshold spread [V] -> progressive width

    # --- per-cycle threshold means (V_h scale; calibrated so the APPLIED
    #     V_set/V_reset land on 1.30 / -1.07 through the series divider) ---
    Vth_set0: float = 1.30     # mean SET threshold on applied V [V]
    Vth_reset0: float = 1.075  # mean |RESET| threshold on applied V [V]
    m_set: float = 4.6         # Weibull shape -> CV(V_set); CV~=sqrt(G(1+2/m)/G(1+1/m)^2-1)
    m_reset: float = 4.8       # Weibull shape -> CV(V_reset)
    rho_acf: float = 0.20      # AR(1) on per-cycle threshold -> lag-1 ACF

    # --- variability widths: CALIBRATED (sigma_lnG, sigma_Gon) ---
    sigma_lnG: float = 0.52    # per-cycle log-conductance residual -> sigma_lnR_HRS
    sigma_Gon: float = 0.0     # per-cycle LRS conductance-lift log-spread -> R_LRS CV
    # --- FIXED inputs (NOT calibrated, NOT emergent): a measurement-noise proxy ---
    icc_noise: float = 0.010   # transistor Isat noise floor; model I_cc CV ends ~3%
    dirichlet_conc: float = 0.6  # patch-weight concentration (few dominant weak links)

    # --- thermal (documented assumptions; need variable-T data to pin) ---
    T0: float = 300.0
    Rth: float = 3.0e5
    Tmax: float = 1500.0

    # --- endurance damage (R5), calibrated last on the 53-cycle sequence ---
    kappa_dmg: float = 0.0     # damage accumulation rate
    cE: float = 0.0            # D -> SET threshold drift [V per unit D]
    cf: float = 0.0            # D -> phi_floor rise (R_HRS down)
    cg: float = 0.0            # D -> Gon degradation (R_LRS up)

    def to_npz(self, path):
        np.savez(path, **{k: v for k, v in asdict(self).items()})

    @classmethod
    def from_npz(cls, path):
        d = dict(np.load(path))
        return cls(**{k: (int(v) if k == "K" else float(v)) for k, v in d.items()})


# ----------------------------------------------------------------------------
# conduction
def _theta(phi, p):
    """Per-patch HRS->LRS weight. Linear (p_perc=1) by default; a Bruggeman-style
    exponent>1 sharpens the percolation knee (enable only with area-scaling data)."""
    return phi if p.p_perc == 1.0 else np.power(np.clip(phi, 0, 1), p.p_perc)


def G_ensemble(phi, lng, w, p, Gon_eff):
    """Area-summed TAT prefactor (independent of V_h) -> hoisted out of the
    divider bisection for speed.  I_hBN(V_h) = G_ens * sinh(alpha*V_h)."""
    return p.I_s * np.sum(w * np.exp(lng) * (1.0 + (Gon_eff - 1.0) * _theta(phi, p)))


def i_hbn(V_h, phi, lng, w, p, Gon_eff):
    """Area-summed TAT current (scalar V_h)."""
    lim = p.alpha * p.Vclip
    return G_ensemble(phi, lng, w, p, Gon_eff) * np.sinh(np.clip(p.alpha * V_h, -lim, lim))


def i_tr(V_tr, side, p, isat_mult):
    if side == "set":
        Isat, Vk, lam = p.Isat_set, p.Vk_set, p.lam_set
    else:
        Isat, Vk, lam = p.Isat_reset, p.Vk_reset, p.lam_reset
    Vt = abs(V_tr)
    return isat_mult * Isat * (1.0 + lam * Vt) * np.tanh(Vt / Vk)


def divider(V_app, G_ens, p, side, isat_mult, nbis=24):
    """Series load-line: find V_h in [0,|V_app|] with G_ens*sinh(a*V_h)=I_tr(|V_app|-V_h).
    Both branches monotone in V_h -> scalar bisection. Returns (I_dev, V_h_signed)."""
    Va = abs(V_app)
    if Va < 1e-9:
        return 0.0, 0.0
    a = p.alpha
    lim = a * p.Vclip
    if side == "set":
        Isat, Vk, lam = p.Isat_set, p.Vk_set, p.lam_set
    else:
        Isat, Vk, lam = p.Isat_reset, p.Vk_reset, p.lam_reset
    Isat *= isat_mult
    lo, hi = 0.0, Va
    for _ in range(nbis):
        mid = 0.5 * (lo + hi)
        vtr = Va - mid
        ihb = G_ens * np.sinh(min(a * mid, lim))
        itr = Isat * (1.0 + lam * vtr) * np.tanh(vtr / Vk)
        if ihb - itr < 0:
            lo = mid
        else:
            hi = mid
    Vh = 0.5 * (lo + hi)
    Idev = G_ens * np.sinh(min(a * Vh, lim))
    return Idev, np.sign(V_app) * Vh


# ----------------------------------------------------------------------------
# kinetics: mean-field soft breakdown.  The defect state is driven by the
# APPLIED terminal stress V_app (the soft-degradation field stress), while the
# series transistor independently limits the CURRENT — this decouples state
# evolution from the post-breakdown V_h collapse, giving a reproducible LRS.
# Patches cross a SPREAD of thresholds -> phi_bar(V) is a smooth (progressive)
# sigmoid.  Exact exponential-Euler keeps phi in [phi_floor,1] for any rate.
def step_phi(phi, V_app, T, Vth_patch, side, p):
    if side == "set":                                  # generation toward 1
        arr = np.exp((p.Ea_set / KB) * (1.0 / p.T0 - 1.0 / T))
        drive = np.sinh(np.clip(p.beta_set * (V_app - Vth_patch), -39, 39))
        g = p.Kc_set * arr * np.clip(drive, 0, None)
        a, b = g, g
    else:                                              # recovery toward floor
        arr = np.exp((p.Ea_reset / KB) * (1.0 / p.T0 - 1.0 / T))
        drive = np.sinh(np.clip(p.beta_reset * (abs(V_app) - Vth_patch), -39, 39))
        r = p.Kc_reset * arr * np.clip(drive, 0, None)
        a, b = r * p.phi_floor, r
    out = phi.copy()
    nz = b > 1e-12
    e = np.exp(-b[nz])
    out[nz] = phi[nz] * e + (a[nz] / b[nz]) * (1.0 - e)
    return np.clip(out, p.phi_floor, 1.0)


# ----------------------------------------------------------------------------
def triangle(vpeak, step=0.02):
    # up[-2::-1] drops the duplicated apex point (avoids dx=0 in downstream
    # np.gradient and a redundant double-dwell at the peak)
    up = np.arange(0, vpeak + np.sign(vpeak) * 1e-9, np.sign(vpeak) * step)
    return np.concatenate([up, up[-2::-1]])


def run_sweep(Vwave, phi0, lng, w, p, side, isat_mult, Vth_c, dtheta, Gon_eff):
    """Integrate phi over a voltage waveform; return I_dev, V_h, phi_bar arrays."""
    phi = phi0.copy()
    n = len(Vwave)
    I = np.empty(n); Vh = np.empty(n); pb = np.empty(n)
    Vth_patch = Vth_c + dtheta            # per-patch thresholds this cycle
    elng = np.exp(lng)
    for k, Va in enumerate(Vwave):
        G_ens = p.I_s * np.sum(w * elng * (1.0 + (Gon_eff - 1.0) * _theta(phi, p)))
        Idev, vh = divider(Va, G_ens, p, side, isat_mult)
        T = min(p.T0 + p.Rth * abs(Idev * vh), p.Tmax)
        phi = step_phi(phi, Va, T, Vth_patch, side, p)   # state driven by V_app
        I[k], Vh[k], pb[k] = Idev, vh, float(np.sum(w * phi))
    return I, Vh, pb, phi


# ----------------------------------------------------------------------------
def make_frozen(p, rng):
    """Frozen device structure (same physical cell): patch weights + thresholds.
    Physical correlation: heavier patches are WEAK LINKS that break FIRST, so
    their threshold offset is lower (anti-correlated with weight). This makes the
    dominant patch always switch -> reproducible LRS -> tame R_LRS spread, while
    sub-dominant patches switching at a spread of thresholds keep the transition
    progressive."""
    w = rng.dirichlet(np.full(p.K, p.dirichlet_conc))
    z = rng.normal(0, 1, p.K)                          # idiosyncratic spread
    wz = (w - w.mean()) / (w.std() + 1e-12)            # standardized weight
    dtheta = p.sigma_theta * (0.7 * (-wz) + 0.7 * z)   # weak links break first
    dtheta -= np.sum(w * dtheta)                       # zero area-weighted mean
    return w, dtheta


def simulate_cycles(p, n_cycles=53, seed=0):
    """Sequential 53-cycle Monte-Carlo for ONE cell (C2C-dominant).
    Per cycle, draw C2C: threshold (AR(1) Weibull), ln-G residual, Isat noise.
    Accumulate endurance damage D across cycles."""
    rng = np.random.default_rng(seed)
    w, dtheta = make_frozen(p, rng)
    D = 0.0
    prev_set = p.Vth_set0
    prev_rst = p.Vth_reset0
    cycles = []
    # Weibull scale eta so that mean = Vth0: mean = eta*Gamma(1+1/m)
    from math import gamma
    eta_set = p.Vth_set0 / gamma(1 + 1 / p.m_set)
    eta_rst = p.Vth_reset0 / gamma(1 + 1 / p.m_reset)
    phi = np.full(p.K, p.phi_floor)
    for c in range(n_cycles):
        # --- per-cycle C2C draws ---
        wbl_s = eta_set * rng.weibull(p.m_set)
        wbl_r = eta_rst * rng.weibull(p.m_reset)
        # AR(1) for lag-1 ACF around the (damage-drifted) mean
        mean_set = p.Vth_set0 + p.cE * D
        Vth_set_c = mean_set + p.rho_acf * (prev_set - mean_set) + \
            np.sqrt(1 - p.rho_acf ** 2) * (wbl_s - p.Vth_set0)
        Vth_rst_c = p.Vth_reset0 + p.rho_acf * (prev_rst - p.Vth_reset0) + \
            np.sqrt(1 - p.rho_acf ** 2) * (wbl_r - p.Vth_reset0)
        prev_set, prev_rst = Vth_set_c, Vth_rst_c
        lng = rng.normal(0, p.sigma_lnG, p.K)         # C2C conductance residual
        isat_mult = rng.normal(1.0, p.icc_noise)      # I_cc 1% noise
        floor_eff = min(p.phi_floor + p.cf * D, 0.5)
        # per-cycle LRS conductance-lift spread (breakdown-configuration C2C);
        # acts only in LRS (phi>0), leaves the HRS read at phi=floor untouched
        Gon_eff = max(p.Gon * np.exp(rng.normal(0, p.sigma_Gon)) * (1 - p.cg * D), 1.0)
        pp = p
        # reset phi to pristine floor at the start of each SET (cell is in HRS)
        phi = np.full(p.K, floor_eff)
        # --- SET sweep 0->+5->0 ---
        Vs = triangle(5.0)
        Is, Vhs, pbs, phi = run_sweep(Vs, phi, lng, w, pp, "set", isat_mult,
                                      Vth_set_c, dtheta, Gon_eff)
        dphi_set = abs(pbs[len(Vs) // 2] - pbs[0])
        # --- RESET sweep 0->-1.7->0 ---
        Vr = triangle(-1.7)
        Ir, Vhr, pbr, phi = run_sweep(Vr, phi, lng, w, pp, "reset", isat_mult,
                                      Vth_rst_c, dtheta, Gon_eff)
        dphi_rst = abs(pbr[len(Vr) // 2] - pbr[0])
        # endurance damage
        D += p.kappa_dmg * (dphi_set + dphi_rst)
        cycles.append(dict(Vs=Vs, Is=Is, pbs=pbs, Vr=Vr, Ir=Ir, pbr=pbr,
                           Vth_set_c=Vth_set_c, Vth_rst_c=Vth_rst_c, D=D))
    return cycles, dict(w=w, dtheta=dtheta)
