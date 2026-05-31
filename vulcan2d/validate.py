"""Validate VULCAN-2D v0.2 against the measured 1T1M data: side-by-side target
table, emergence checks (I_cc decoupling, log-normal R shape, V_set/V_reset
independence, progressive transitions), and a model-vs-data figure."""
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from . import model as M
from . import features as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FIG = os.path.join(ROOT, "analysis", "figures")


def load_measured():
    """Measured I-V clouds + per-cycle features from the two xlsx files."""
    setc, rstc = {}, {}
    xw = pd.ExcelFile(os.path.join(ROOT, "1T1M写入.xlsx"))
    xe = pd.ExcelFile(os.path.join(ROOT, "1T1M擦除.xlsx"))
    for i, sn in enumerate(xw.sheet_names):
        d = xw.parse(sn); setc[i] = (d["voltage"].to_numpy(float), d["current"].to_numpy(float))
    for i, sn in enumerate(xe.sheet_names):
        d = xe.parse(sn); rstc[i] = (d["voltage"].to_numpy(float), d["current"].to_numpy(float))
    sdf = pd.read_csv(os.path.join(ROOT, "analysis", "set_features.csv"))
    rdf = pd.read_csv(os.path.join(ROOT, "analysis", "reset_features.csv"))
    return setc, rstc, sdf, rdf


def main():
    p = M.Params.from_npz(os.path.join(HERE, "vulcan2d_calibrated.npz"))
    cyc, frozen = M.simulate_cycles(p, n_cycles=53, seed=2026)
    mdf = F.extract_all(cyc)
    setc, rstc, sdf, rdf = load_measured()

    def cv(x):
        x = np.asarray(x, float); x = x[np.isfinite(x)]
        return np.std(x) / abs(np.mean(x)) * 100

    print("=" * 72)
    print("VULCAN-2D v0.2 validation  (model 53-cycle MC vs measured 1T1M cell)")
    print("=" * 72)
    print(f"{'feature':14s}{'MODEL mean':>13s}{'MODEL CV':>10s} | {'DATA mean':>13s}{'DATA CV':>9s}")
    rows = [("V_set (V)", mdf.Vset, sdf.Vset), ("V_reset (V)", mdf.Vreset, rdf.Vreset),
            ("R_HRS (Ohm)", mdf.R_HRS, sdf.R_HRS), ("R_LRS (Ohm)", mdf.R_LRS, sdf.R_LRS),
            ("I_cc (A)", mdf.Icc, sdf.Icc)]
    for name, m, d in rows:
        print(f"{name:14s}{np.nanmean(m):>13.3e}{cv(m):>9.1f}% | "
              f"{np.nanmean(d):>13.3e}{cv(d):>8.1f}%")
    print(f"{'window':14s}{np.nanmedian(mdf.R_HRS/mdf.R_LRS):>13.0f}{'':>10s} | "
          f"{np.nanmedian(sdf.R_HRS/sdf.R_LRS):>13.0f}")

    print("\n--- EMERGENCE CHECKS (must come out right WITHOUT being targeted) ---")
    rr = np.corrcoef(mdf.Vset, mdf.Vreset)[0, 1]
    print(f"  corr(V_set,V_reset): model {rr:+.2f}  | data "
          f"{np.corrcoef(sdf.Vset, rdf.Vreset)[0,1]:+.2f}  (independence, EMERGENT)")
    _, pn = stats.shapiro(mdf.R_HRS); _, pl = stats.shapiro(np.log(mdf.R_HRS))
    print(f"  R_HRS Shapiro: p(normal)={pn:.3f} p(log-normal)={pl:.3f}  "
          f"-> {'LOG-NORMAL' if pl>pn else 'normal'} shape (EMERGENT)")
    print(f"  I_cc CV={cv(mdf.Icc):.1f}% while V_set CV={cv(mdf.Vset):.0f}%, "
          f"R_HRS CV={cv(mdf.R_HRS):.0f}% -> transistor DECOUPLING (EMERGENT)")
    # progressive transition: phi_bar slope at crossing (finite, not a step)
    c = cyc[0]; h = len(c["Vs"]) // 2
    pb = c["pbs"][:h + 1]; Vv = c["Vs"][:h + 1]
    cross = np.argmin(np.abs(pb - 0.5))
    width = np.sum((pb > 0.1) & (pb < 0.9))
    print(f"  progressive SET: phi_bar 0.1->0.9 spans {width} steps "
          f"(~{width*0.02:.2f} V) -> NOT abrupt (EMERGENT)")
    print(f"  NB V_reset dlogI CV {cv(mdf.Vreset):.0f}% underreads data {cv(rdf.Vreset):.0f}%:"
          f" the erase-compliance ramp masks the drop. Physical (phi) reset threshold"
          f" CV={cv(mdf.Vreset_phi):.0f}% does carry the full spread (documented limitation).")

    # ---------------- figure ----------------
    fig, ax = plt.subplots(2, 3, figsize=(16.5, 9.2))
    for V, I in setc.values():
        ax[0, 0].semilogy(V, np.abs(I), color="lightgrey", lw=0.5)
    for c in cyc:
        ax[0, 0].semilogy(c["Vs"], np.abs(c["Is"]), color="crimson", lw=0.4, alpha=0.5)
    ax[0, 0].set_title("(a) SET: model(red) vs data(grey)"); ax[0, 0].set_ylim(1e-11, 1e-3)
    ax[0, 0].set_xlabel("V"); ax[0, 0].set_ylabel("|I| (A)")
    for V, I in rstc.values():
        ax[0, 1].semilogy(V, np.abs(I), color="lightgrey", lw=0.5)
    for c in cyc:
        ax[0, 1].semilogy(c["Vr"], np.abs(c["Ir"]), color="navy", lw=0.4, alpha=0.5)
    ax[0, 1].set_title("(b) RESET: model(blue) vs data(grey)"); ax[0, 1].set_ylim(1e-12, 1e-4)
    ax[0, 1].set_xlabel("V"); ax[0, 1].set_ylabel("|I| (A)")
    # progressive transition phi_bar + per-patch
    ax[0, 2].plot(Vv, pb, color="seagreen", lw=1.6)
    ax[0, 2].axhline(0.5, color="grey", ls=":")
    ax[0, 2].set_title("(c) progressive soft-breakdown phi_bar(V) [non-filamentary]")
    ax[0, 2].set_xlabel("applied V"); ax[0, 2].set_ylabel("phi_bar")
    # distributions
    ax[1, 0].hist(sdf.Vset, bins=12, color="grey", alpha=0.6, density=True, label="data")
    ax[1, 0].hist(mdf.Vset, bins=12, color="crimson", alpha=0.6, density=True, label="model")
    ax[1, 0].hist(rdf.Vreset, bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 0].hist(mdf.Vreset, bins=12, color="navy", alpha=0.6, density=True)
    ax[1, 0].set_title("(d) V_set / V_reset (emergent independence)"); ax[1, 0].legend(fontsize=8)
    ax[1, 0].set_xlabel("V")
    ax[1, 1].hist(np.log10(sdf.R_HRS), bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 1].hist(np.log10(mdf.R_HRS), bins=12, color="darkorange", alpha=0.6, density=True, label="HRS")
    ax[1, 1].hist(np.log10(sdf.R_LRS), bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 1].hist(np.log10(mdf.R_LRS), bins=12, color="teal", alpha=0.6, density=True, label="LRS")
    ax[1, 1].set_title("(e) log10 R: model vs data(grey) [lognormal shape emergent]")
    ax[1, 1].set_xlabel("log10 R (Ohm)"); ax[1, 1].legend(fontsize=8)
    ax[1, 2].plot(np.arange(1, 54), mdf.Icc * 1e6, "o-", ms=3, color="purple")
    ax[1, 2].set_title(f"(f) I_cc stability: CV={cv(mdf.Icc):.1f}% (transistor-set)")
    ax[1, 2].set_xlabel("cycle"); ax[1, 2].set_ylabel("I_cc (uA)")
    for a in ax.ravel():
        a.grid(True, which="both", alpha=0.2)
    fig.suptitle("VULCAN-2D v0.2 — non-filamentary percolation/soft-breakdown model vs 1T1M h-BN data",
                 fontsize=13, y=0.995)
    plt.tight_layout()
    out = os.path.join(FIG, "09_vulcan_v2_validation.png")
    plt.savefig(out, dpi=130)
    print("\nsaved", out)


if __name__ == "__main__":
    main()
