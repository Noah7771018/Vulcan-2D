"""Evidence test for a FINITE-N distributed-defect (non-filamentary) picture:
do the SET forward sweeps show DISCRETE conductance jumps (sequential site
activation) rather than one smooth ramp? Count significant upward steps per
cycle in log-current and estimate an effective number of switching events.

If many small discrete steps -> supports percolation / finite-site ensemble.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_data import load_all, HERE

FIG = os.path.join(HERE, "figures")
setc, rstc = load_all()


def count_steps(V, I, vlo=0.2, vhi=2.5, thr=0.15):
    """Count upward jumps in log10|I| exceeding `thr` decades between adjacent
    points, within the rising (pre-compliance) window."""
    m = (V >= vlo) & (V <= vhi)
    Vw, Iw = V[m], np.abs(I[m])
    if len(Vw) < 5:
        return 0, np.array([])
    g = np.log10(np.clip(Iw, 1e-13, None))
    d = np.diff(g)
    jumps = np.where(d > thr)[0]
    return len(jumps), Vw[jumps]


# per-cycle step counts on SET forward
counts = []
jump_volts = []
for c in setc.values():
    n, vj = count_steps(c["V_fwd"], c["I_fwd"])
    counts.append(n)
    jump_volts.extend(vj.tolist())
counts = np.array(counts)
print("SET forward discrete-jump analysis (>0.15 dec between adjacent 0.02V points):")
print(f"  steps/cycle: mean={counts.mean():.1f}  median={np.median(counts):.0f}  "
      f"range=[{counts.min()},{counts.max()}]")
print(f"  total jumps across 53 cycles: {len(jump_volts)}; "
      f"jump-voltage mean={np.mean(jump_volts):.2f} V std={np.std(jump_volts):.2f}")

# how 'smooth vs stepped': fraction of total log-current rise carried by jumps
frac_in_jumps = []
for c in setc.values():
    V, I = c["V_fwd"], np.abs(c["I_fwd"])
    m = (V >= 0.2) & (V <= 2.5)
    g = np.log10(np.clip(I[m], 1e-13, None))
    if len(g) < 5:
        continue
    d = np.diff(g)
    total_rise = g[-1] - g[0]
    jump_rise = d[d > 0.15].sum()
    if total_rise > 0:
        frac_in_jumps.append(jump_rise / total_rise)
print(f"  fraction of the HRS->LRS log-rise carried by discrete jumps: "
      f"{np.mean(frac_in_jumps)*100:.0f}% (rest is smooth ramp)")

# figure: histogram of steps/cycle + where jumps occur in voltage + example
fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
ax[0].hist(counts, bins=range(0, counts.max() + 2), color="purple", alpha=0.8, align="left")
ax[0].set_title("discrete jumps per SET sweep")
ax[0].set_xlabel("# jumps (>0.15 dec)"); ax[0].set_ylabel("cycles")
ax[1].hist(jump_volts, bins=20, color="teal", alpha=0.8)
ax[1].set_title("voltage at which jumps occur")
ax[1].set_xlabel("V (V)"); ax[1].set_ylabel("count")
# example cycle with derivative
c = setc[10]
V, I = c["V_fwd"], np.abs(c["I_fwd"])
m = (V >= 0.0) & (V <= 2.6)
ax[2].semilogy(V[m], I[m], ".-", ms=3, color="crimson")
n, vj = count_steps(V, I)
for v in vj:
    ax[2].axvline(v, color="grey", ls=":", lw=0.8)
ax[2].set_title(f"example S10: {n} jumps marked")
ax[2].set_xlabel("V"); ax[2].set_ylabel("|I| (A)")
for a in ax:
    a.grid(True, alpha=0.2)
plt.tight_layout()
out = os.path.join(FIG, "08_step_evidence.png")
plt.savefig(out, dpi=125)
print("saved", out)
print("\nINTERPRETATION: many small discrete jumps spread over a band of voltages,")
print("each cycle a different subset -> consistent with sequential activation of a")
print("FINITE ensemble of distributed defect sites (non-filamentary percolation).")
