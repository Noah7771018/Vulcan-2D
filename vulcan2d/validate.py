"""Validate VULCAN-2D v0.3 against the measured 1T1M data."""
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
VALIDATION_SEED = 110  # nearest sequence to the 12-seed ensemble median


def load_measured():
    """Measured I-V clouds + per-cycle features from the two xlsx files."""
    setc, rstc = {}, {}
    xw = pd.ExcelFile(os.path.join(ROOT, "1T1M写入.xlsx"))
    xe = pd.ExcelFile(os.path.join(ROOT, "1T1M擦除.xlsx"))
    srows, rrows = [], []
    for i, sn in enumerate(xw.sheet_names):
        d = xw.parse(sn)
        V, I = d["voltage"].to_numpy(float), d["current"].to_numpy(float)
        setc[i] = (V, I)
        srows.append(F.set_feat(V, I))
    for i, sn in enumerate(xe.sheet_names):
        d = xe.parse(sn)
        V, I = d["voltage"].to_numpy(float), d["current"].to_numpy(float)
        rstc[i] = (V, I)
        rrows.append(F.reset_feat(V, I))
    sdf, rdf = pd.DataFrame(srows), pd.DataFrame(rrows)
    return setc, rstc, sdf, rdf


def _branch(V, I, forward):
    apex = int(np.argmax(np.abs(V)))
    sl = slice(None, apex + 1) if forward else slice(apex, None)
    return np.abs(V[sl]), np.abs(I[sl])


def _median_log_branch(curves, grid):
    rows = []
    for V, I in curves:
        order = np.argsort(V)
        rows.append(np.interp(grid, V[order], np.log10(np.clip(I[order], 1e-13, None))))
    return np.nanmedian(rows, axis=0)


def branch_error(measured, model, vmax):
    grid = np.arange(0.1, vmax + 1e-9, 0.02)
    error = _median_log_branch(model, grid) - _median_log_branch(measured, grid)
    return np.sqrt(np.mean(error ** 2)), np.mean(error)


def slope(values, log=False):
    y = np.asarray(values, float)
    if log:
        y = np.log(np.clip(y, 1e-30, None))
    return np.polyfit(np.arange(len(y), dtype=float), y, 1)[0]


def main():
    os.makedirs(FIG, exist_ok=True)
    p = M.Params.from_npz(os.path.join(HERE, "vulcan2d_calibrated.npz"))
    cyc, frozen = M.simulate_cycles(p, n_cycles=53, seed=VALIDATION_SEED)
    mdf = F.extract_all(cyc)
    setc, rstc, sdf, rdf = load_measured()

    def cv(x):
        x = np.asarray(x, float); x = x[np.isfinite(x)]
        return np.std(x) / abs(np.mean(x)) * 100

    print("=" * 72)
    print(f"VULCAN-2D v0.3 validation  (representative seed {VALIDATION_SEED}, 53 cycles)")
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

    print("\n--- FULL-LOOP SHAPE (median log10|I| error, decades) ---")
    specs = [
        ("SET forward", [_branch(*x, True) for x in setc.values()],
         [_branch(c["Vs"], c["Is"], True) for c in cyc], 5.0),
        ("SET return", [_branch(*x, False) for x in setc.values()],
         [_branch(c["Vs"], c["Is"], False) for c in cyc], 5.0),
        ("RESET forward", [_branch(*x, True) for x in rstc.values()],
         [_branch(c["Vr"], c["Ir"], True) for c in cyc], 1.7),
        ("RESET return", [_branch(*x, False) for x in rstc.values()],
         [_branch(c["Vr"], c["Ir"], False) for c in cyc], 1.7),
    ]
    for name, measured, model, vmax in specs:
        rmse, bias = branch_error(measured, model, vmax)
        print(f"  {name:14s} RMSE={rmse:.3f}, bias={bias:+.3f}")

    print("\n--- ENDURANCE TRENDS (model | data) ---")
    print(f"  V_set       {slope(mdf.Vset):+.4g} | {slope(sdf.Vset):+.4g} V/cycle")
    print(f"  ln R_HRS    {slope(mdf.R_HRS, True):+.4g} | "
          f"{slope(sdf.R_HRS, True):+.4g} /cycle")
    print(f"  ln R_LRS    {slope(mdf.R_LRS, True):+.4g} | "
          f"{slope(sdf.R_LRS, True):+.4g} /cycle")

    print("\n--- MODEL-STRUCTURE CHECKS ---")
    rr = np.corrcoef(mdf.Vset, mdf.Vreset)[0, 1]
    print(f"  corr(V_set,V_reset): model {rr:+.2f}  | data "
          f"{np.corrcoef(sdf.Vset, rdf.Vreset)[0,1]:+.2f}  (independent draws; by construction)")
    _, pn = stats.shapiro(mdf.R_HRS); _, pl = stats.shapiro(np.log(mdf.R_HRS))
    print(f"  R_HRS Shapiro: p(normal)={pn:.3f} p(log-normal)={pl:.3f}  "
          f"-> {'log-normal-like' if pl>pn else 'normal-like'} (descriptive, not unique)")
    print(f"  I_cc CV={cv(mdf.Icc):.1f}% while V_set CV={cv(mdf.Vset):.0f}%, "
          f"R_HRS CV={cv(mdf.R_HRS):.0f}% -> transistor decoupling (structural consequence)")
    # progressive transition: phi_bar slope at crossing (finite, not a step)
    c = cyc[0]; h = len(c["Vs"]) // 2
    pb = c["pbs"][:h + 1]; Vv = c["Vs"][:h + 1]
    cross = np.argmin(np.abs(pb - 0.5))
    width = np.sum((pb > 0.1) & (pb < 0.9))
    print(f"  progressive SET: phi_bar 0.1->0.9 spans {width} steps "
          f"(~{width*0.02:.2f} V) -> progressive by distributed thresholds")
    print("  thermal feedback disabled: current data contain no variable-T constraint")

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
    ax[0, 2].set_title("(c) progressive distributed-path state phi_bar(V)")
    ax[0, 2].set_xlabel("applied V"); ax[0, 2].set_ylabel("phi_bar")
    # distributions
    ax[1, 0].hist(sdf.Vset, bins=12, color="grey", alpha=0.6, density=True, label="data")
    ax[1, 0].hist(mdf.Vset, bins=12, color="crimson", alpha=0.6, density=True, label="model")
    ax[1, 0].hist(rdf.Vreset, bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 0].hist(mdf.Vreset, bins=12, color="navy", alpha=0.6, density=True)
    ax[1, 0].set_title("(d) V_set / V_reset distributions"); ax[1, 0].legend(fontsize=8)
    ax[1, 0].set_xlabel("V")
    ax[1, 1].hist(np.log10(sdf.R_HRS), bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 1].hist(np.log10(mdf.R_HRS), bins=12, color="darkorange", alpha=0.6, density=True, label="HRS")
    ax[1, 1].hist(np.log10(sdf.R_LRS), bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 1].hist(np.log10(mdf.R_LRS), bins=12, color="teal", alpha=0.6, density=True, label="LRS")
    ax[1, 1].set_title("(e) log10 R: model vs data(grey)")
    ax[1, 1].set_xlabel("log10 R (Ohm)"); ax[1, 1].legend(fontsize=8)
    ax[1, 2].plot(np.arange(1, 54), mdf.Icc * 1e6, "o-", ms=3, color="purple")
    ax[1, 2].set_title(f"(f) I_cc stability: CV={cv(mdf.Icc):.1f}% (transistor-set)")
    ax[1, 2].set_xlabel("cycle"); ax[1, 2].set_ylabel("I_cc (uA)")
    for a in ax.ravel():
        a.grid(True, which="both", alpha=0.2)
    fig.suptitle("VULCAN-2D v0.3 - distributed soft-breakdown model vs 1T1M h-BN data",
                 fontsize=13, y=0.995)
    plt.tight_layout()
    out = os.path.join(FIG, "10_vulcan_v3_validation.png")
    plt.savefig(out, dpi=130)
    print("\nsaved", out)


if __name__ == "__main__":
    main()
