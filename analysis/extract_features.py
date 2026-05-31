"""Extract per-cycle switching features from all 53 SET and RESET cycles.

Definitions
-----------
SET forward (0->+5):  HRS -> LRS.  V_set = V where d(log10|I|)/dV is maximal
                      (steepest current rise) within the rising window.
RESET forward (0->-1.7): LRS -> HRS. V_reset = V where d(log10|I|)/dV is most
                      negative (steepest current drop).
Read resistances at |Vread| = 0.2 V:
  R_HRS  from SET-forward branch (pristine HRS) near +0.2 V
  R_LRS  from SET-return  branch (just-set LRS) near +0.2 V
  Also R_LRS' from RESET-forward near -0.2 V, R_HRS' from RESET-return near -0.2 V
I_cc   = compliance current = |I| at the apex of SET forward (V=+5).
"""
import os
import numpy as np
import pandas as pd
from load_data import load_all, HERE

VREAD = 0.2


def _smooth(y, w=5):
    if len(y) < w:
        return y
    k = np.ones(w) / w
    return np.convolve(y, k, mode="same")


def _at_voltage(V, I, vtarget, tol=0.06):
    """|I| nearest to vtarget; returns (V_used, I_used) or None."""
    idx = np.argmin(np.abs(V - vtarget))
    if abs(V[idx] - vtarget) > tol:
        return None
    return V[idx], abs(I[idx])


def set_features(c):
    Vf, If = c["V_fwd"], np.abs(c["I_fwd"])
    logI = np.log10(np.clip(If, 1e-13, None))
    dlog = np.gradient(_smooth(logI), Vf)
    # restrict to rising region below compliance merge (V in [0.3, 3])
    win = (Vf > 0.3) & (Vf < 3.0)
    iset = np.argmax(np.where(win, dlog, -np.inf))
    Vset = Vf[iset]
    Icc = abs(c["I_fwd"][-1])  # at apex +5 V
    hrs = _at_voltage(Vf, If, VREAD)
    lrs = _at_voltage(c["V_ret"], np.abs(c["I_ret"]), VREAD)
    return dict(
        Vset=Vset,
        Icc=Icc,
        R_HRS=(hrs[0] / hrs[1]) if hrs else np.nan,
        I_HRS=hrs[1] if hrs else np.nan,
        R_LRS=(lrs[0] / lrs[1]) if lrs else np.nan,
        I_LRS=lrs[1] if lrs else np.nan,
    )


def reset_features(c):
    Vf, If = c["V_fwd"], np.abs(c["I_fwd"])  # 0 -> -1.7
    logI = np.log10(np.clip(If, 1e-13, None))
    dlog = np.gradient(_smooth(logI), Vf)  # V decreasing, so drop => dlog/dV>0 large
    win = (Vf < -0.5) & (Vf > -1.7)
    # steepest drop as V goes more negative: large positive d(logI)/dV
    irst = np.argmax(np.where(win, dlog, -np.inf))
    Vreset = Vf[irst]
    lrs = _at_voltage(Vf, If, -VREAD)            # LRS just before reset
    hrs = _at_voltage(c["V_ret"], np.abs(c["I_ret"]), -VREAD)  # HRS after reset
    return dict(
        Vreset=Vreset,
        R_LRS_r=(abs(lrs[0]) / lrs[1]) if lrs else np.nan,
        I_LRS_r=lrs[1] if lrs else np.nan,
        R_HRS_r=(abs(hrs[0]) / hrs[1]) if hrs else np.nan,
        I_HRS_r=hrs[1] if hrs else np.nan,
    )


def main():
    setc, rstc = load_all()
    srow = [dict(cycle=k, **set_features(c)) for k, c in setc.items()]
    rrow = [dict(cycle=k, **reset_features(c)) for k, c in rstc.items()]
    sdf = pd.DataFrame(srow)
    rdf = pd.DataFrame(rrow)
    sdf.to_csv(os.path.join(HERE, "set_features.csv"), index=False)
    rdf.to_csv(os.path.join(HERE, "reset_features.csv"), index=False)

    def stat(name, x):
        x = np.asarray(x, float); x = x[np.isfinite(x)]
        cv = np.std(x) / np.abs(np.mean(x)) * 100
        return (f"  {name:10s} mean={np.mean(x):.3e}  std={np.std(x):.2e}  "
                f"CV={cv:5.1f}%  [min {np.min(x):.2e}, max {np.max(x):.2e}]")

    print("=== SET features (n=%d) ===" % len(sdf))
    for col in ["Vset", "Icc", "R_HRS", "R_LRS", "I_HRS", "I_LRS"]:
        print(stat(col, sdf[col]))
    print("  HRS/LRS resistance ratio (median):",
          f"{np.nanmedian(sdf.R_HRS/sdf.R_LRS):.1f}")
    print("=== RESET features (n=%d) ===" % len(rdf))
    for col in ["Vreset", "R_LRS_r", "R_HRS_r", "I_LRS_r", "I_HRS_r"]:
        print(stat(col, rdf[col]))
    return sdf, rdf


if __name__ == "__main__":
    main()
