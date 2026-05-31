"""Look at representative single cycles in detail: forward vs return half
sweeps, both log and linear, for SET and RESET."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_data import load_all, HERE

FIG = os.path.join(HERE, "figures")
setc, rstc = load_all()

cyc = [1, 10, 25, 50]
fig, axes = plt.subplots(2, 4, figsize=(18, 9))

for j, k in enumerate(cyc):
    c = setc[k]
    ax = axes[0, j]
    ax.semilogy(c["V_fwd"], np.abs(c["I_fwd"]), ".-", ms=2, lw=0.6,
                color="crimson", label="forward 0→5")
    ax.semilogy(c["V_ret"], np.abs(c["I_ret"]), ".-", ms=2, lw=0.6,
                color="orange", label="return 5→0")
    ax.set_title(f"SET cycle S{k}")
    ax.set_xlabel("V"); ax.set_ylabel("|I| (A)")
    ax.set_ylim(1e-11, 1e-3); ax.grid(True, which="both", alpha=0.2)
    if j == 0: ax.legend(fontsize=8)

for j, k in enumerate(cyc):
    c = rstc[k]
    ax = axes[1, j]
    ax.semilogy(c["V_fwd"], np.abs(c["I_fwd"]), ".-", ms=2, lw=0.6,
                color="navy", label="forward 0→-1.7")
    ax.semilogy(c["V_ret"], np.abs(c["I_ret"]), ".-", ms=2, lw=0.6,
                color="dodgerblue", label="return -1.7→0")
    ax.set_title(f"RESET cycle R{k}")
    ax.set_xlabel("V"); ax.set_ylabel("|I| (A)")
    ax.set_ylim(1e-14, 1e-4); ax.grid(True, which="both", alpha=0.2)
    if j == 0: ax.legend(fontsize=8)

plt.tight_layout()
out = os.path.join(FIG, "02_single_cycles.png")
plt.savefig(out, dpi=120)
print("saved", out)

# Print the SET forward trajectory of S1 to see where current ramps
c = setc[1]
vf, iff = c["V_fwd"], np.abs(c["I_fwd"])
print("\nSET S1 forward, every 25th point (V, I):")
for idx in range(0, len(vf), 25):
    print(f"  V={vf[idx]:+.2f}  I={iff[idx]:.3e}")
