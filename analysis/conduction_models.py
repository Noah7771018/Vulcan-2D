"""Identify the conduction mechanism in HRS and LRS by fitting candidate
physical models to voltage-binned MEDIAN I-V curves (robust to C2C noise).

Branches used:
  HRS  = SET forward, 0 < V < ~0.9 (pristine high-resistance, before set)
  LRS  = SET return, 0 < V < 5     (just-set low-resistance, compliance side)

Candidate models (positive-bias magnitude):
  Ohmic      : I = G*V                       -> log-log slope 1
  SCLC       : I = k*V^m                      -> log-log slope m (~2 trap-free)
  Schottky   : ln I   = a + b*sqrt(V)         (b>0)  thermionic over barrier
  Poole-Frenkel: ln(I/V) = a + b*sqrt(V)      (b>0)  trap-assisted bulk emission
  Hopping    : ln I   = a + b*V               nearest-neighbour hopping / t.a.t
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from numpy.polynomial import polynomial as P
from load_data import load_all, HERE

FIG = os.path.join(HERE, "figures")


def median_branch(curves, which, vlo, vhi, vstep=0.04):
    """Bin |I| by voltage across all cycles, return (Vc, Imed, Ilo, Ihi)."""
    edges = np.arange(vlo, vhi + vstep, vstep)
    centers = 0.5 * (edges[:-1] + edges[1:])
    buckets = [[] for _ in centers]
    for c in curves.values():
        V = c[which]
        I = np.abs(c["I_fwd"] if which == "V_fwd" else c["I_ret"])
        Va = np.abs(V)
        for v, i in zip(Va, I):
            if vlo <= v < vhi:
                b = min(int((v - vlo) / vstep), len(centers) - 1)
                buckets[b].append(i)
    med = np.array([np.median(b) if b else np.nan for b in buckets])
    lo = np.array([np.percentile(b, 16) if b else np.nan for b in buckets])
    hi = np.array([np.percentile(b, 84) if b else np.nan for b in buckets])
    ok = np.isfinite(med)
    return centers[ok], med[ok], lo[ok], hi[ok]


def r2(y, yhat):
    ss = np.sum((y - np.mean(y)) ** 2)
    return 1 - np.sum((y - yhat) ** 2) / ss if ss > 0 else np.nan


def fit_linear(x, y):
    b, a = np.polyfit(x, y, 1)[0], np.polyfit(x, y, 1)[1]
    return a, b, r2(y, a + b * x)


def analyse(tag, V, I):
    out = {}
    lnI = np.log(I)
    # Ohmic / SCLC: log-log
    a, m, R = fit_linear(np.log(V), lnI)
    out["SCLC/power (slope m)"] = (m, R)
    # Schottky: lnI vs sqrt(V)
    a, b, R = fit_linear(np.sqrt(V), lnI)
    out["Schottky (b)"] = (b, R)
    # Poole-Frenkel: ln(I/V) vs sqrt(V)
    a, b, R = fit_linear(np.sqrt(V), np.log(I / V))
    out["Poole-Frenkel (b)"] = (b, R)
    # Hopping: lnI vs V
    a, b, R = fit_linear(V, lnI)
    out["Hopping (b)"] = (b, R)
    print(f"\n--- {tag}  (n={len(V)} bins, V {V.min():.2f}..{V.max():.2f}) ---")
    for k, (p, R) in out.items():
        print(f"   {k:24s} param={p:+.3f}  R2={R:.4f}")
    return out


def main():
    setc, rstc = load_all()
    # HRS: pristine forward, safely below the (mean) set voltage ~1.3 V
    Vh, Ih, Hlo, Hhi = median_branch(setc, "V_fwd", 0.08, 0.95)
    # LRS: set return branch (compliance side), full range but skip tiny V noise
    Vl, Il, Llo, Lhi = median_branch(setc, "V_ret", 0.10, 5.0)

    print("=" * 64)
    print("HRS (SET forward, pre-set):  model discrimination")
    analyse("HRS forward", Vh, Ih)
    print("=" * 64)
    print("LRS (SET return, post-set):  model discrimination")
    analyse("LRS return", Vl, Il)

    # ---- plots of the diagnostic linearisations ----
    fig, ax = plt.subplots(2, 3, figsize=(16, 9))
    # HRS panels
    ax[0, 0].loglog(Vh, Ih, "o", ms=4, color="crimson")
    ax[0, 0].set_title("HRS  log-log (SCLC/power)"); ax[0, 0].set_xlabel("V"); ax[0, 0].set_ylabel("|I|")
    ax[0, 1].plot(np.sqrt(Vh), np.log(Ih), "o", ms=4, color="crimson")
    ax[0, 1].set_title("HRS  Schottky: ln I vs √V"); ax[0, 1].set_xlabel("√V"); ax[0, 1].set_ylabel("ln I")
    ax[0, 2].plot(np.sqrt(Vh), np.log(Ih / Vh), "o", ms=4, color="crimson")
    ax[0, 2].set_title("HRS  Poole-Frenkel: ln(I/V) vs √V"); ax[0, 2].set_xlabel("√V"); ax[0, 2].set_ylabel("ln(I/V)")
    # LRS panels
    ax[1, 0].loglog(Vl, Il, "o", ms=4, color="navy")
    ax[1, 0].set_title("LRS  log-log (power/ohmic)"); ax[1, 0].set_xlabel("V"); ax[1, 0].set_ylabel("|I|")
    ax[1, 1].plot(Vl, Il * 1e6, "o", ms=4, color="navy")
    ax[1, 1].set_title("LRS  linear I-V (ohmic?)"); ax[1, 1].set_xlabel("V"); ax[1, 1].set_ylabel("I (µA)")
    ax[1, 2].plot(np.sqrt(Vl), np.log(Il / Vl), "o", ms=4, color="navy")
    ax[1, 2].set_title("LRS  PF: ln(I/V) vs √V"); ax[1, 2].set_xlabel("√V"); ax[1, 2].set_ylabel("ln(I/V)")
    for a in ax.ravel():
        a.grid(True, which="both", alpha=0.2)
    plt.tight_layout()
    out = os.path.join(FIG, "03_conduction_linearisations.png")
    plt.savefig(out, dpi=120)
    print("\nsaved", out)

    # save median branches for reuse
    np.savez(os.path.join(HERE, "median_branches.npz"),
             Vh=Vh, Ih=Ih, Hlo=Hlo, Hhi=Hhi, Vl=Vl, Il=Il, Llo=Llo, Lhi=Lhi)


if __name__ == "__main__":
    main()
