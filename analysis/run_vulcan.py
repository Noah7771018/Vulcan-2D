"""Calibrate the VULCAN-2D dynamic model to the measured 1T1M targets, run a
53-cycle Monte-Carlo, and validate: loop overlay + emergent distributions."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import vulcan_model as vm
from load_data import load_all, HERE

FIG = os.path.join(HERE, "figures")
TARGET = dict(Vset=1.30, Vreset=-1.07)


def _mean_threshold(p, which, nu0, n=9):
    """Mean Vset or Vreset over n noiseless cycles at given nu0."""
    pp = vm.Params(**{**p.__dict__})
    pp.sigma_Ea = 0.0; pp.sigma_g0 = 0.0; pp.icc_noise = 0.0
    if which == "set":
        pp.nu0_set = nu0
    else:
        pp.nu0_reset = nu0
    rng = np.random.default_rng(0)
    vals = []
    for _ in range(n):
        c = vm.simulate_cycle(pp, rng)
        vals.append(c["Vset"] if which == "set" else c["Vreset"])
    return np.nanmean(vals)


def calibrate_nu0(p, which, target, lo=1e11, hi=1e16):
    """Bisect on nu0 (Vthr decreases as nu0 grows)."""
    tlo = _mean_threshold(p, which, hi)   # high nu0 -> low |Vthr|
    thi = _mean_threshold(p, which, lo)
    for _ in range(30):
        mid = np.sqrt(lo * hi)
        v = _mean_threshold(p, which, mid)
        if not np.isfinite(v) or abs(v) > abs(target):
            lo = mid                      # no switch / |V| too high -> raise nu0
        else:
            hi = mid                      # switched too early -> lower nu0
    return np.sqrt(lo * hi)


def main():
    p = vm.Params()
    print("Calibrating kinetics to Vset=%.2f, Vreset=%.2f ..." % (TARGET["Vset"], TARGET["Vreset"]))
    p.nu0_set = calibrate_nu0(p, "set", TARGET["Vset"])
    p.nu0_reset = calibrate_nu0(p, "reset", TARGET["Vreset"])
    print("  nu0_set=%.3e   nu0_reset=%.3e" % (p.nu0_set, p.nu0_reset))

    # ---- Monte-Carlo 53 cycles ----
    rng = np.random.default_rng(2026)
    cycles = [vm.simulate_cycle(p, rng) for _ in range(53)]
    F = pd.DataFrame([{k: c[k] for k in ["Vset", "Vreset", "R_HRS", "R_LRS", "Icc"]}
                      for c in cycles])

    # ---- measured references ----
    setc, rstc = load_all()
    sdf = pd.read_csv(os.path.join(HERE, "set_features.csv"))
    rdf = pd.read_csv(os.path.join(HERE, "reset_features.csv"))

    def cv(x):
        x = np.asarray(x, float); x = x[np.isfinite(x)]
        return np.std(x) / abs(np.mean(x)) * 100

    print("\n%-10s %12s %12s | %12s %12s" % ("feature", "MODEL mean", "MODEL CV", "DATA mean", "DATA CV"))
    rows = [("Vset", F.Vset, sdf.Vset), ("Vreset", F.Vreset, rdf.Vreset),
            ("R_HRS", F.R_HRS, sdf.R_HRS), ("R_LRS", F.R_LRS, sdf.R_LRS),
            ("Icc", F.Icc, sdf.Icc)]
    for name, m, d in rows:
        print("%-10s %12.3e %11.1f%% | %12.3e %11.1f%%"
              % (name, np.nanmean(m), cv(m), np.nanmean(d), cv(d)))
    print("\nemergent checks:")
    print("  window R_HRS/R_LRS  model=%.0f  data~600" % (np.nanmedian(F.R_HRS / F.R_LRS)))
    mm = np.isfinite(F.Vset) & np.isfinite(F.Vreset)
    rr = np.corrcoef(F.Vset[mm], F.Vreset[mm])[0, 1]
    print("  corr(Vset,Vreset)   model=%+.2f  data~0 (independent)" % rr)
    print("  log-normality R_HRS: sigma_lnR model=%.2f  data~0.52"
          % np.std(np.log(F.R_HRS)))

    # ---- figure ----
    fig, ax = plt.subplots(2, 3, figsize=(16.5, 9.2))
    # loop overlay SET
    for c in setc.values():
        ax[0, 0].semilogy(c["V"], np.abs(c["I"]), color="lightgrey", lw=0.5)
    for c in cycles:
        ax[0, 0].semilogy(c["Vs"], np.abs(c["Is"]), color="crimson", lw=0.4, alpha=0.5)
    ax[0, 0].set_title("(a) SET: model(red) vs data(grey)")
    ax[0, 0].set_xlabel("V"); ax[0, 0].set_ylabel("|I| (A)"); ax[0, 0].set_ylim(1e-11, 1e-3)
    # loop overlay RESET
    for c in rstc.values():
        ax[0, 1].semilogy(c["V"], np.abs(c["I"]), color="lightgrey", lw=0.5)
    for c in cycles:
        ax[0, 1].semilogy(c["Vr"], np.abs(c["Ir"]), color="navy", lw=0.4, alpha=0.5)
    ax[0, 1].set_title("(b) RESET: model(blue) vs data(grey)")
    ax[0, 1].set_xlabel("V"); ax[0, 1].set_ylabel("|I| (A)"); ax[0, 1].set_ylim(1e-12, 1e-4)
    # gap & temperature dynamics (one cycle)
    c0 = cycles[0]
    axg = ax[0, 2]; axt = axg.twinx()
    t = np.arange(len(c0["Vs"]))
    axg.plot(t, c0["gs"], color="seagreen", lw=1.4, label="gap g")
    axt.plot(t, c0["Ts"], color="firebrick", lw=1.0, alpha=0.7, label="T")
    axg.set_title("(c) internal state during SET sweep")
    axg.set_xlabel("step"); axg.set_ylabel("gap g (nm)", color="seagreen")
    axt.set_ylabel("T (K)", color="firebrick")
    # Vset dist
    ax[1, 0].hist(sdf.Vset, bins=12, color="grey", alpha=0.6, density=True, label="data")
    ax[1, 0].hist(F.Vset, bins=12, color="crimson", alpha=0.6, density=True, label="model")
    ax[1, 0].set_title("(d) V_set distribution (emergent)"); ax[1, 0].set_xlabel("V_set (V)"); ax[1, 0].legend()
    # Vreset dist
    ax[1, 1].hist(rdf.Vreset, bins=12, color="grey", alpha=0.6, density=True, label="data")
    ax[1, 1].hist(F.Vreset, bins=12, color="navy", alpha=0.6, density=True, label="model")
    ax[1, 1].set_title("(e) V_reset distribution (emergent)"); ax[1, 1].set_xlabel("V_reset (V)"); ax[1, 1].legend()
    # R distributions
    ax[1, 2].hist(np.log10(sdf.R_HRS), bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 2].hist(np.log10(F.R_HRS), bins=12, color="darkorange", alpha=0.6, density=True, label="HRS model")
    ax[1, 2].hist(np.log10(sdf.R_LRS), bins=12, color="grey", alpha=0.6, density=True)
    ax[1, 2].hist(np.log10(F.R_LRS), bins=12, color="teal", alpha=0.6, density=True, label="LRS model")
    ax[1, 2].set_title("(f) log10 R: model vs data(grey)"); ax[1, 2].set_xlabel("log10 R (Ω)"); ax[1, 2].legend()
    for a in ax.ravel():
        a.grid(True, which="both", alpha=0.2)
    plt.tight_layout()
    out = os.path.join(FIG, "07_vulcan_dynamic.png")
    plt.savefig(out, dpi=130)
    print("\nsaved", out)
    # persist calibrated params
    np.savez(os.path.join(HERE, "vulcan_calibrated.npz"), **p.__dict__)


if __name__ == "__main__":
    main()
