"""VULCAN-2D — dynamic electro-thermal device model for the 1T1M h-BN memristor.

SIM2RRAM-style coupled solve, with physics swapped for 2D-layered material:

  state  : tunnelling gap g(t)  [nm]   (g_min = filament closed/LRS,
                                        g_max = ruptured/HRS)
  (1) transport  I(V,g): h-BN gap conduction (sinh trap-assisted tunnelling,
        exponential in gap width) in SERIES with the 1T transistor (bottleneck
        blend) -> HRS = h-BN limited, LRS = transistor limited.
  (2) kinetics   dg/dt = -nu0*exp(-Ea/kT)*sinh(beta*V)
        +V shrinks the gap (SET), -V grows it (RESET), V=0 -> holds (non-vol).
  (3) Joule heat T = T0 + Rth*|I*V|     -> feeds back into the Arrhenius rate.
  (4) variability: per-cycle random Ea (=> V_set/V_reset spread, independent
        for SET vs RESET) and random initial gap (=> log-normal R_HRS).

The headline data regularities are *emergent*, not hand-sampled:
  R2 (I_cc CV~1%)  : LRS = deterministic transistor branch
  R4 (R log-normal): R_HRS ~ exp(g/g_c), g normal  -> log-normal
  R4 (Vset⊥Vreset) : independent Ea draws on the two half-loops
"""
from dataclasses import dataclass, field
import numpy as np

KB = 8.617333e-5  # eV/K


@dataclass
class Params:
    # --- transport ---
    I_s0: float = 8.3e-6        # h-BN gap prefactor [A]
    alpha: float = 6.75         # sinh field coeff [1/V]  (from HRS fit)
    g_c: float = 0.20           # tunnelling decay length [nm]
    g_min: float = 0.10         # closed-filament gap [nm]  (LRS)
    g_rup: float = 2.00         # mean ruptured gap [nm]    (HRS, sets R_HRS)
    g_max: float = 2.60         # ceiling [nm] (above mean so +sigma not truncated)
    # transistor output branch (log-space fits to SET-return / RESET-fwd LRS):
    #   I_t = Isat*(1+lam|V|)*tanh(|V|/Vk)  -- hits both 0.2 V read and 5 V apex
    Isat_set: float = 3.70e-7   # WRITE side [A]
    Vk_set: float = 0.759
    lam_set: float = 27.4
    Isat_reset: float = 2.94e-8  # ERASE side [A] (lower gate -> ~1-2 uA plateau)
    Vk_reset: float = 0.355
    lam_reset: float = 119.2
    # --- kinetics ---
    Ea0: float = 1.00           # migration activation energy [eV]
    nu0_set: float = 5e12       # attempt rate, SET (calibrated) [nm/step]
    nu0_reset: float = 5e12     # attempt rate, RESET (calibrated) [nm/step]
    beta_set: float = 3.0       # field coeff SET [1/V]
    beta_reset: float = 3.0     # field coeff RESET [1/V]
    # --- thermal ---
    T0: float = 300.0           # ambient [K]
    Rth: float = 3.0e5          # thermal resistance [K/W]
    Tmax: float = 1500.0        # clamp [K]
    # --- variability (1-sigma) ---
    sigma_Ea: float = 0.025     # eV  -> Vset/Vreset spread (CV ~25%)
    sigma_g0: float = 0.090     # nm  -> log-normal R_HRS (sigma_lnR = s/g_c ~0.52)
    sigma_gon: float = 0.26     # nm  -> C2C closed-gap spread -> R_LRS read CV
    icc_noise: float = 0.01     # fractional compliance noise (R2)


def transistor(V, tp):
    Isat, Vk, lam = tp
    return Isat * (1.0 + lam * np.abs(V)) * np.tanh(np.abs(V) / Vk)


def conduction(V, g, p, tp):
    """Series bottleneck of h-BN gap branch and the 1T transistor branch.
    tp = (Isat, Vk, lam) selects the WRITE- or ERASE-side compliance."""
    aV = np.abs(V)
    I_hbn = p.I_s0 * np.exp(-(g - p.g_min) / p.g_c) * np.sinh(p.alpha * aV)
    I_t = transistor(V, tp)
    denom = I_hbn + I_t + 1e-30
    I_blend = (I_hbn * I_t) / denom                  # -> min(branch) limited
    return np.sign(V) * I_blend


def _rate(V, g, p, Ea, T, nu0, beta):
    """dg per step. +V shrinks gap (SET), -V grows it (RESET)."""
    return -nu0 * np.exp(-Ea / (KB * T)) * np.sinh(beta * V)


def run_sweep(Vwave, g0, p, Ea, tp, nu0, beta, dt=1.0, g_floor=None):
    """Integrate g over a voltage waveform; return I(t), g(t), T(t).
    g_floor sets the minimum gap (per-cycle closed gap -> R_LRS spread)."""
    if g_floor is None:
        g_floor = p.g_min
    g = float(g0)
    I = np.empty_like(Vwave)
    G = np.empty_like(Vwave)
    Tarr = np.empty_like(Vwave)
    for k, V in enumerate(Vwave):
        Ik = conduction(V, g, p, tp)
        T = min(p.T0 + p.Rth * abs(Ik * V), p.Tmax)
        dg = _rate(V, g, p, Ea, T, nu0, beta) * dt
        dg = np.clip(dg, -0.1, 0.1)               # per-step stability clamp
        g = float(np.clip(g + dg, g_floor, p.g_max))
        I[k], G[k], Tarr[k] = Ik, g, T
    return I, G, Tarr


def triangle(vpeak, step=0.02):
    up = np.arange(0, vpeak + np.sign(vpeak) * 1e-9, np.sign(vpeak) * step)
    return np.concatenate([up, up[::-1]])


def simulate_cycle(p, rng, vset_peak=5.0, vreset_peak=-1.7):
    """One full bipolar loop. Returns dict with waveforms + extracted features.
    Variability injected into Ea (per half-loop, independent) and g_init."""
    # per-cycle closed gap (filament quality) -> R_LRS read variability
    g_on = float(np.clip(rng.normal(p.g_min, p.sigma_gon), p.g_min, p.g_rup - 0.3))
    # --- SET half-loop (start ruptured) ---
    Ea_s = p.Ea0 + rng.normal(0, p.sigma_Ea)
    g_init = np.clip(rng.normal(p.g_rup, p.sigma_g0), p.g_min, p.g_max)
    tp_s = (p.Isat_set * (1 + rng.normal(0, p.icc_noise)), p.Vk_set, p.lam_set)
    Vw_s = triangle(vset_peak)
    I_s, g_s, T_s = run_sweep(Vw_s, g_init, p, Ea_s, tp_s,
                              p.nu0_set, p.beta_set, g_floor=g_on)
    # --- RESET half-loop (start closed at g_on) ---
    Ea_r = p.Ea0 + rng.normal(0, p.sigma_Ea)
    tp_r = (p.Isat_reset * (1 + rng.normal(0, p.icc_noise)), p.Vk_reset, p.lam_reset)
    Vw_r = triangle(vreset_peak)
    I_r, g_r, T_r = run_sweep(Vw_r, g_on, p, Ea_r, tp_r,
                              p.nu0_reset, p.beta_reset)
    feat = _features(Vw_s, g_s, Vw_r, g_r, I_s, I_r, p)
    return dict(Vs=Vw_s, Is=I_s, gs=g_s, Ts=T_s,
                Vr=Vw_r, Ir=I_r, gr=g_r, Tr=T_r, **feat)


def _features(Vs, gs, Vr, gr, Is, Ir, p):
    gmid = 0.5 * (p.g_min + p.g_rup)
    half = len(Vs) // 2
    # V_set: first +V on SET upsweep where gap crosses midpoint (closing)
    up = slice(0, half)
    idx = np.where(gs[up] <= gmid)[0]
    Vset = Vs[idx[0]] if len(idx) else np.nan
    # V_reset: first -V on RESET downsweep where gap crosses midpoint (opening)
    halfr = len(Vr) // 2
    dn = slice(0, halfr)
    idxr = np.where(gr[dn] >= gmid)[0]
    Vreset = Vr[idxr[0]] if len(idxr) else np.nan
    # read resistances at 0.2 V
    def R_at(Vw, I, vt):
        j = np.argmin(np.abs(Vw - vt))
        return abs(vt) / (abs(I[j]) + 1e-30)
    return dict(Vset=Vset, Vreset=Vreset,
                R_HRS=R_at(Vs, Is, 0.2),       # pristine, SET upsweep
                R_LRS=R_at(Vs, Is, 0.2) if False else _RLRS(Vs, Is),
                Icc=abs(Is[half]))             # at +5 V apex


def _RLRS(Vs, Is):
    half = len(Vs) // 2
    ret = slice(half, len(Vs))
    Vw, I = Vs[ret], Is[ret]
    j = np.argmin(np.abs(Vw - 0.2))
    return 0.2 / (abs(I[j]) + 1e-30)
