"""Publication-style summary figure tying together: measured bipolar loop,
the two fitted conduction mechanisms, switching-voltage statistics, the
endurance trend, and the generative-model overlay."""
import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_data import load_all, HERE

FIG = os.path.join(HERE, "figures")
setc, rstc = load_all()
sdf = pd.read_csv(os.path.join(HERE, "set_features.csv"))
rdf = pd.read_csv(os.path.join(HERE, "reset_features.csv"))
mp = np.load(os.path.join(HERE, "model_params.npz"))
d = np.load(os.path.join(HERE, "median_branches.npz"))
Vh, Ih, Vl, Il = d["Vh"], d["Ih"], d["Vl"], d["Il"]

hrs = lambda V, Is, a: Is * np.sinh(a * V)
lrs = lambda V, Isat, Vk, lam: Isat * (1 + lam * np.abs(V)) * np.tanh(np.abs(V) / Vk)
phr = curve_fit(lambda v, Is, a: np.log(hrs(v, Is, a)), Vh, np.log(Ih), p0=[6e-10, 6.7])[0]
plf = curve_fit(lrs, Vl, Il, p0=[3e-5, .6, .05], maxfev=20000)[0]

fig = plt.figure(figsize=(16.5, 9.5))
gs = fig.add_gridspec(2, 3, hspace=0.32, wspace=0.28)

# (a) measured bipolar loop
ax = fig.add_subplot(gs[0, 0])
for c in setc.values():
    ax.semilogy(c["V"], np.abs(c["I"]), color="crimson", lw=0.3, alpha=0.25)
for c in rstc.values():
    ax.semilogy(c["V"], np.abs(c["I"]), color="navy", lw=0.3, alpha=0.25)
ax.axvline(sdf.Vset.mean(), color="crimson", ls="--", lw=1)
ax.axvline(rdf.Vreset.mean(), color="navy", ls="--", lw=1)
ax.text(sdf.Vset.mean()+0.1, 2e-4, f"$V_{{set}}$≈{sdf.Vset.mean():.2f}V", color="crimson", fontsize=9)
ax.text(rdf.Vreset.mean()-2.4, 2e-4, f"$V_{{reset}}$≈{rdf.Vreset.mean():.2f}V", color="navy", fontsize=9)
ax.set_title("(a) Measured bipolar loop (53 cycles)")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("|I| (A)")
ax.set_ylim(1e-11, 1e-3); ax.set_xlim(-2.2, 5.2); ax.grid(True, which="both", alpha=0.2)

# (b) HRS mechanism
ax = fig.add_subplot(gs[0, 1])
ax.semilogy(Vh, Ih, "o", ms=4, color="darkorange", label="median data")
vv = np.linspace(0.05, 0.95, 100)
ax.semilogy(vv, hrs(vv, *phr), "-", color="k", lw=1.6,
            label=f"$I=I_s\\sinh(\\alpha V)$\n$R^2_{{log}}$=0.998")
ax.set_title("(b) HRS = symmetric trap-assisted tunneling")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("|I| (A)")
ax.grid(True, which="both", alpha=0.2); ax.legend(fontsize=9)

# (c) LRS mechanism (linear, transistor output char)
ax = fig.add_subplot(gs[0, 2])
ax.plot(Vl, Il*1e6, "o", ms=3, color="teal", label="median data")
vv = np.linspace(0.05, 5, 200)
ax.plot(vv, lrs(vv, *plf)*1e6, "-", color="k", lw=1.6,
        label=f"transistor $I_{{sat}}\\tanh$ model\n$R^2$=0.989")
ax.axvline(plf[1], color="grey", ls=":", lw=1)
ax.text(plf[1]+0.1, 5, "triode→saturation\nknee $V_k$", fontsize=8, color="grey")
ax.set_title("(c) LRS = 1T transistor-limited output")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("I (µA)")
ax.grid(True, alpha=0.2); ax.legend(fontsize=9, loc="lower right")

# (d) switching voltage distributions
ax = fig.add_subplot(gs[1, 0])
ax.hist(sdf.Vset, bins=13, color="crimson", alpha=0.75, label=f"$V_{{set}}$ CV={sdf.Vset.std()/sdf.Vset.mean()*100:.0f}%")
ax.hist(rdf.Vreset, bins=13, color="navy", alpha=0.75, label=f"$V_{{reset}}$ CV={abs(rdf.Vreset.std()/rdf.Vreset.mean())*100:.0f}%")
ax.set_title("(d) Switching-voltage variability (C2C)")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("count"); ax.legend(fontsize=9); ax.grid(True, alpha=0.2)

# (e) endurance: resistance window & compliance stability
ax = fig.add_subplot(gs[1, 1])
ax.semilogy(sdf.cycle, sdf.R_HRS, "o-", ms=3, color="darkorange", label="$R_{HRS}$")
ax.semilogy(sdf.cycle, sdf.R_LRS, "o-", ms=3, color="teal", label="$R_{LRS}$")
ax.set_title("(e) Endurance: window slowly narrows\n($R_{HRS}\\downarrow$, $R_{LRS}\\uparrow$)")
ax.set_xlabel("cycle #"); ax.set_ylabel("R @0.2V (Ω)"); ax.legend(fontsize=9); ax.grid(True, which="both", alpha=0.2)
ax2 = ax.twinx()
ax2.plot(sdf.cycle, sdf.Icc*1e6, ".", color="purple", alpha=0.5)
ax2.set_ylabel("$I_{cc}$ (µA, CV 1%)", color="purple"); ax2.tick_params(axis="y", colors="purple")

# (f) model overlay
ax = fig.add_subplot(gs[1, 2])
rng = np.random.default_rng(3)
Gh, bh, Isat, Vk, lam = mp["Gh"], mp["bh"], mp["Isat"], mp["Vk"], mp["lam"]
for c in setc.values():
    ax.semilogy(c["V"], np.abs(c["I"]), color="lightgrey", lw=0.5)
for _ in range(40):
    Vset = rng.normal(1.30, 0.33); Ghc = Gh*np.exp(rng.normal(0, .516)); Isc = rng.normal(Isat, .01*Isat)
    Vup = np.arange(0, 5.0001, .02); st = 0; I = []
    for V in Vup:
        if not st and V >= Vset: st = 1
        I.append(lrs(V, Isc, Vk, lam) if st else hrs(V, Ghc, bh))
    ax.semilogy(Vup, np.abs(I), color="crimson", lw=0.4, alpha=0.5)
    ax.semilogy(Vup[::-1], np.abs(lrs(Vup[::-1], Isc, Vk, lam)), color="orange", lw=0.4, alpha=0.5)
ax.set_title("(f) Generative model (red) vs data (grey)")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("|I| (A)")
ax.set_ylim(1e-11, 1e-3); ax.grid(True, which="both", alpha=0.2)

fig.suptitle("1T1M h-BN memristor — data regularities & explanatory models (VULCAN-2D seed)",
             fontsize=14, y=0.98)
out = os.path.join(FIG, "06_SUMMARY.png")
plt.savefig(out, dpi=135, bbox_inches="tight")
print("saved", out)
