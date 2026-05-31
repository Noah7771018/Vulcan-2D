"""Overview plots: all 53 SET and RESET cycles overlaid, plus a combined
bipolar I-V (|I| log scale) to compare with the reference image."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_data import load_all, HERE

FIG = os.path.join(HERE, "figures")
setc, rstc = load_all()

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# --- SET cycles (positive sweep) ---
ax = axes[0]
for i, c in setc.items():
    ax.semilogy(c["V"], np.abs(c["I"]), color="crimson", lw=0.4, alpha=0.35)
ax.set_title(f"SET (write)  0→+5→0 V  ·  {len(setc)} cycles")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("|Current| (A)")
ax.set_ylim(1e-11, 1e-3); ax.grid(True, which="both", alpha=0.2)

# --- RESET cycles (negative sweep) ---
ax = axes[1]
for i, c in rstc.items():
    ax.semilogy(c["V"], np.abs(c["I"]), color="navy", lw=0.4, alpha=0.35)
ax.set_title(f"RESET (erase)  0→-1.7→0 V  ·  {len(rstc)} cycles")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("|Current| (A)")
ax.set_ylim(1e-11, 1e-3); ax.grid(True, which="both", alpha=0.2)

# --- Combined bipolar |I|-V ---
ax = axes[2]
for i, c in setc.items():
    ax.semilogy(c["V"], np.abs(c["I"]), color="crimson", lw=0.3, alpha=0.25)
for i, c in rstc.items():
    ax.semilogy(c["V"], np.abs(c["I"]), color="navy", lw=0.3, alpha=0.25)
ax.set_title("Combined bipolar loop (red=SET, blue=RESET)")
ax.set_xlabel("Voltage (V)"); ax.set_ylabel("|Current| (A)")
ax.set_ylim(1e-11, 1e-3); ax.set_xlim(-2.5, 5.2); ax.grid(True, which="both", alpha=0.2)

plt.tight_layout()
out = os.path.join(FIG, "01_overview.png")
plt.savefig(out, dpi=130)
print("saved", out)

# quick stats on current ranges
import numpy as np
for name, coll in [("SET", setc), ("RESET", rstc)]:
    allI = np.concatenate([np.abs(c["I"]) for c in coll.values()])
    print(f"{name}: |I| min={allI.min():.2e} max={allI.max():.2e} "
          f"median={np.median(allI):.2e}")
