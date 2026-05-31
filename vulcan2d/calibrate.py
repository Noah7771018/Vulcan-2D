"""Ordered calibration of VULCAN-2D v0.2 to the measured 1T1M targets.

Follows the design's calibration plan: fix transport, then pin each macroscopic
target with ONE knob via 1-D bisection / proportional update, in an order chosen
so later steps don't disturb earlier ones.  Writes vulcan2d_calibrated.npz.
"""
import os
import numpy as np
from math import gamma
from . import model as M
from . import features as F

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = dict(Vset=1.298, Vset_cv=25.2, Vreset=-1.075, Vreset_cv=24.3,
              R_HRS=2.045e8, sigma_lnR_HRS=0.521, R_LRS=2.939e5, R_LRS_cv=28.4,
              Icc=5.146e-5, window=600.0)


SEED = 2026   # single physical cell -> one frozen structure throughout


def run(p, n=40, seed=SEED):
    cyc, _ = M.simulate_cycles(p, n_cycles=n, seed=seed)
    return F.extract_all(cyc)


def feat(df, col):
    return F.summary(df, col)


def bisect_knob(p, attr, target, getter, lo, hi, iters=11, n=24, tol=0.015,
                increasing=True):
    """Bisect Params.attr in [lo,hi] so getter(run(p))==target.
    increasing=True means getter rises with attr."""
    val = np.nan
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        setattr(p, attr, mid)
        val = getter(run(p, n=n))
        if abs(val - target) / (abs(target) + 1e-12) < tol:
            break
        if (val > target) == increasing:
            hi = mid
        else:
            lo = mid
    return getattr(p, attr), val


def cv_from_m(m):
    return np.sqrt(gamma(1 + 2 / m) / gamma(1 + 1 / m) ** 2 - 1) * 100


def main():
    p = M.Params()
    print("VULCAN-2D v0.2 calibration")
    print("-" * 60)

    # ---- structural params FIRST (threshold calibration last, undisturbed) ----
    # STEP 1: Weibull shapes for the switching-voltage CVs (analytic)
    for attr, key in [("m_set", "Vset_cv"), ("m_reset", "Vreset_cv")]:
        ms = np.linspace(2, 12, 400)
        cvs = np.array([cv_from_m(m) for m in ms])
        setattr(p, attr, float(ms[np.argmin(np.abs(cvs - TARGET[key]))]))
    print(f"STEP1 m_set={p.m_set:.2f} (CV {cv_from_m(p.m_set):.1f}%) "
          f"m_reset={p.m_reset:.2f} (CV {cv_from_m(p.m_reset):.1f}%)")

    # STEP 2: sigma_lnG -> sigma_lnR_HRS (lognormal-R width; shape emergent)
    v, got = bisect_knob(p, "sigma_lnG", TARGET["sigma_lnR_HRS"],
                         lambda df: feat(df, "R_HRS")["sigma_ln"], 0.2, 1.4)
    print(f"STEP2 sigma_lnG={v:.3f} -> sigma_lnR_HRS={got:.3f}")

    # STEP 3: I_s -> R_HRS MEAN. NB sigma_lnG (STEP2) shifts the lognormal mean
    # via E[exp(lng)]=exp(sigma^2/2), so I_s is pinned AFTER sigma_lnG to absorb it.
    v, got = bisect_knob(p, "I_s", TARGET["R_HRS"],
                         lambda df: feat(df, "R_HRS")["mean"], 3e-10, 1.2e-9,
                         increasing=False)
    print(f"STEP3 I_s={v:.3e} -> R_HRS={got:.2e}")

    # STEP 4a: Gon -> R_LRS mean (LRS = transistor R_on + h-BN series)
    v, got = bisect_knob(p, "Gon", TARGET["R_LRS"],
                         lambda df: feat(df, "R_LRS")["mean"], 5e2, 6e3,
                         increasing=False)
    print(f"STEP4a Gon={v:.0f} -> R_LRS={got:.2e}")
    # STEP 4b: sigma_Gon -> R_LRS CV (per-cycle breakdown-config spread; LRS-only)
    v, got = bisect_knob(p, "sigma_Gon", TARGET["R_LRS_cv"],
                         lambda df: feat(df, "R_LRS")["cv"], 0.0, 1.2)
    print(f"STEP4b sigma_Gon={v:.3f} -> R_LRS CV={got:.1f}%")
    # STEP 4c: re-pin R_LRS mean (sigma_Gon lifts the lognormal mean)
    v, got = bisect_knob(p, "Gon", TARGET["R_LRS"],
                         lambda df: feat(df, "R_LRS")["mean"], 5e2, 8e3,
                         increasing=False)
    print(f"STEP4c Gon={v:.0f} -> R_LRS={got:.2e} (CV {feat(run(p),'R_LRS')['cv']:.0f}%)")

    # ---- threshold means LAST (structural params now fixed) ----
    # STEP 5: bisect SET threshold mean -> applied V_set mean
    v, got = bisect_knob(p, "Vth_set0", TARGET["Vset"],
                         lambda df: feat(df, "Vset")["mean"], 0.6, 2.4)
    print(f"STEP5 Vth_set0={v:.3f} -> V_set={got:.3f}")

    # STEP 6: bisect RESET threshold mean -> applied |V_reset|
    v, got = bisect_knob(p, "Vth_reset0", abs(TARGET["Vreset"]),
                         lambda df: -feat(df, "Vreset")["mean"], 0.3, 1.8)
    print(f"STEP6 Vth_reset0={v:.3f} -> |V_reset|={got:.3f}")

    # final report
    df = run(p, n=53, seed=2026)
    print("-" * 60)
    print(f"{'feature':10s}{'MODEL':>14s}{'CV%':>8s} | {'TARGET':>12s}")
    rows = [("Vset", "Vset", "mean"), ("Vreset", "Vreset", "mean"),
            ("R_HRS", "R_HRS", "mean"), ("R_LRS", "R_LRS", "mean"),
            ("Icc", "Icc", "mean")]
    for name, col, _ in rows:
        s = feat(df, col)
        tk = name if name in TARGET else None
        print(f"{name:10s}{s['mean']:>14.3e}{s['cv']:>7.1f}% | "
              f"{TARGET.get(name, float('nan')):>12.3e}")
    print(f"window {np.nanmedian(df.R_HRS/df.R_LRS):.0f} (target ~600)")
    out = os.path.join(HERE, "vulcan2d_calibrated.npz")
    p.to_npz(out)
    print("saved", out)
    return p


if __name__ == "__main__":
    main()
