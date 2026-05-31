"""Cycle-to-cycle (C2C) variability and trend analysis.

Produces:
  - distributions of Vset, Vreset, R_HRS, R_LRS (with normal / lognormal tests)
  - cycle-number trends (drift / endurance) and lag-1 autocorrelation
  - correlation between Vset and resulting LRS, etc.
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_data import HERE

FIG = os.path.join(HERE, "figures")
sdf = pd.read_csv(os.path.join(HERE, "set_features.csv"))
rdf = pd.read_csv(os.path.join(HERE, "reset_features.csv"))


def lognorm_vs_norm(x):
    x = np.abs(x[np.isfinite(x)])
    x = x[x > 0]
    if len(x) < 3:
        return np.nan, np.nan
    _, p_n = stats.shapiro(x)
    _, p_l = stats.shapiro(np.log(x))
    return p_n, p_l


def lag1(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 3:
        return np.nan
    return np.corrcoef(x[:-1], x[1:])[0, 1]


print("=== Distribution / variability summary ===")
for name, x in [("Vset", sdf.Vset.values), ("Vreset", rdf.Vreset.values),
                ("R_HRS", sdf.R_HRS.values), ("R_LRS", sdf.R_LRS.values),
                ("I_HRS", sdf.I_HRS.values), ("I_LRS", sdf.I_LRS.values),
                ("Icc", sdf.Icc.values)]:
    xx = x[np.isfinite(x)]
    cv = np.std(xx) / abs(np.mean(xx)) * 100
    ax_ = np.abs(xx); sigln = np.std(np.log(ax_[ax_ > 0]))
    pn, pl = lognorm_vs_norm(xx)
    better = "lognormal" if pl > pn else "normal"
    print(f"  {name:7s} CV={cv:5.1f}%  sigma_ln={sigln:.3f}  "
          f"lag1-acf={lag1(x):+.2f}  better-fit={better} (p_norm={pn:.3f},p_logn={pl:.3f})")

# trend slopes vs cycle number
print("\n=== Drift vs cycle number (linear slope, Mann-Kendall) ===")
for name, df, col in [("Vset", sdf, "Vset"), ("Vreset", rdf, "Vreset"),
                      ("R_HRS", sdf, "R_HRS"), ("R_LRS", sdf, "R_LRS")]:
    y = df[col].values.astype(float)
    c = df["cycle"].values.astype(float)
    m = np.isfinite(y)
    sl, ic, r, p, se = stats.linregress(c[m], y[m])
    tau, pmk = stats.kendalltau(c[m], y[m])
    print(f"  {name:7s} slope/cycle={sl:+.3e} (p={p:.3f})  "
          f"Kendall_tau={tau:+.2f} (p={pmk:.3f})")

# correlations
print("\n=== Cross-correlations ===")
m = np.isfinite(sdf.Vset) & np.isfinite(sdf.R_LRS)
print(f"  Vset vs R_LRS : r={np.corrcoef(sdf.Vset[m], sdf.R_LRS[m])[0,1]:+.2f}")
m = np.isfinite(sdf.Vset) & np.isfinite(sdf.R_HRS)
print(f"  Vset vs R_HRS : r={np.corrcoef(sdf.Vset[m], sdf.R_HRS[m])[0,1]:+.2f}")
n = min(len(sdf), len(rdf))
print(f"  Vset(n) vs Vreset(n): r="
      f"{np.corrcoef(sdf.Vset[:n], rdf.Vreset[:n])[0,1]:+.2f}")

# ---- figure ----
fig, ax = plt.subplots(2, 3, figsize=(16, 9))
ax[0, 0].hist(sdf.Vset, bins=14, color="crimson", alpha=0.8)
ax[0, 0].axvline(sdf.Vset.mean(), color="k", ls="--")
ax[0, 0].set_title(f"V_set  ({sdf.Vset.mean():.2f}±{sdf.Vset.std():.2f} V)")
ax[0, 0].set_xlabel("V_set (V)")
ax[0, 1].hist(rdf.Vreset, bins=14, color="navy", alpha=0.8)
ax[0, 1].axvline(rdf.Vreset.mean(), color="k", ls="--")
ax[0, 1].set_title(f"V_reset  ({rdf.Vreset.mean():.2f}±{rdf.Vreset.std():.2f} V)")
ax[0, 1].set_xlabel("V_reset (V)")
ax[0, 2].hist(np.log10(sdf.R_HRS), bins=14, color="orange", alpha=0.7, label="HRS")
ax[0, 2].hist(np.log10(sdf.R_LRS), bins=14, color="teal", alpha=0.7, label="LRS")
ax[0, 2].set_title("log10 R_HRS / R_LRS"); ax[0, 2].set_xlabel("log10 R (Ω)"); ax[0, 2].legend()

ax[1, 0].plot(sdf.cycle, sdf.Vset, "o-", color="crimson", ms=4, label="Vset")
ax[1, 0].plot(rdf.cycle, rdf.Vreset, "o-", color="navy", ms=4, label="Vreset")
ax[1, 0].axhline(0, color="grey", lw=0.5)
ax[1, 0].set_title("Switching voltage vs cycle"); ax[1, 0].set_xlabel("cycle"); ax[1, 0].set_ylabel("V"); ax[1, 0].legend()
ax[1, 1].semilogy(sdf.cycle, sdf.R_HRS, "o-", color="orange", ms=4, label="R_HRS")
ax[1, 1].semilogy(sdf.cycle, sdf.R_LRS, "o-", color="teal", ms=4, label="R_LRS")
ax[1, 1].set_title("Read resistance vs cycle (window stability)")
ax[1, 1].set_xlabel("cycle"); ax[1, 1].set_ylabel("R (Ω)"); ax[1, 1].legend()
ax[1, 2].semilogy(sdf.cycle, sdf.Icc, "o-", color="purple", ms=4)
ax[1, 2].set_title(f"Compliance I_cc vs cycle (CV={sdf.Icc.std()/sdf.Icc.mean()*100:.1f}%)")
ax[1, 2].set_xlabel("cycle"); ax[1, 2].set_ylabel("I_cc (A)")
for a in ax.ravel():
    a.grid(True, alpha=0.2)
plt.tight_layout()
out = os.path.join(FIG, "04_variability.png")
plt.savefig(out, dpi=120)
print("\nsaved", out)
