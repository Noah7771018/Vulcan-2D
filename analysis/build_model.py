"""VULCAN-2D seed model: a compact, generative device model for the 1T1M
h-BN memristor that reproduces the full bipolar I-V loop *and* its C2C spread.

Two conduction branches (fitted to the median measured branches):
  HRS  (trap-assisted / Poole-Frenkel form):
        I_hrs(V) = G_h * V * exp(b_h * sqrt(|V|))            [odd in V]
  LRS  (transistor-limited output characteristic):
        I_lrs(V) = sign(V) * Isat * (1+lam*|V|) * tanh(|V|/Vk)
        -> low |V|: ohmic  I≈(Isat/Vk)V ; high |V|: saturation Isat(1+lam|V|)

State machine over a sweep (quasi-static, threshold-triggered):
  SET  forward  (0->+5):  HRS until V>=Vset(random) then LRS
  SET  return   (+5->0):  LRS
  RESET forward (0->-1.7): LRS until V<=Vreset(random) then HRS
  RESET return  (-1.7->0): HRS
Per-cycle randomness from the measured distributions:
  Vset ~ N(1.30,0.33), Vreset ~ N(-1.07,0.26),
  G_h log-normal (sigma_ln(R_HRS)=0.52), Isat ~ N (CV 1%, transistor clamp).
"""
import os
import numpy as np
from scipy.optimize import curve_fit
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from load_data import load_all, HERE

FIG = os.path.join(HERE, "figures")
rng = np.random.default_rng(7)

# ---------- 0. median branches (robust to C2C noise) ----------
setc0, rstc0 = load_all()


def median_branch(curves, which, vlo, vhi, vstep=0.04):
    edges = np.arange(vlo, vhi + vstep, vstep)
    centers = 0.5 * (edges[:-1] + edges[1:])
    buckets = [[] for _ in centers]
    for c in curves.values():
        V = c[which]
        I = np.abs(c["I_fwd"] if which == "V_fwd" else c["I_ret"])
        for v, i in zip(np.abs(V), I):
            if vlo <= v < vhi:
                b = min(int((v - vlo) / vstep), len(centers) - 1)
                buckets[b].append(i)
    med = np.array([np.median(b) if b else np.nan for b in buckets])
    ok = np.isfinite(med)
    return centers[ok], med[ok]


# four physical branches, each under its own measurement bias
Vh, Ih = median_branch(setc0, "V_fwd", 0.08, 0.95)   # SET fwd  -> pristine HRS
Vl, Il = median_branch(setc0, "V_ret", 0.10, 5.0)    # SET ret  -> write-side LRS
Vlr, Ilr = median_branch(rstc0, "V_fwd", 0.10, 0.95)  # RESET fwd-> erase-side LRS (pre-reset)
Vhr, Ihr = median_branch(rstc0, "V_ret", 0.10, 0.95)  # RESET ret-> HRS (post-reset)


def hrs_model(V, Is, a):
    """Symmetric trap-assisted tunneling: odd, through-origin, exp at high field.
    Small-signal ohmic resistance R_HRS(0) = 1/(Is*a)."""
    V = np.asarray(V, float)
    return Is * np.sinh(a * V)


def lrs_model(V, Isat, Vk, lam):
    V = np.asarray(V, float)
    return np.sign(V) * Isat * (1 + lam * np.abs(V)) * np.tanh(np.abs(V) / Vk)


def _logfit(model, V, I, p0):
    p, _ = curve_fit(lambda v, *pp: np.log(model(v, *pp)), V, np.log(I),
                     p0=p0, maxfev=40000)
    return p


def _r2(y, yh):
    return 1 - np.sum((y - yh) ** 2) / np.sum((y - np.mean(y)) ** 2)


# write-side branches
ph = _logfit(hrs_model, Vh, Ih, [6e-10, 6.7])      # SET-fwd HRS (log-space)
pl, _ = curve_fit(lrs_model, Vl, Il, p0=[3e-5, 0.6, 0.05], maxfev=20000)
Gh, bh = ph
Isat, Vk, lam = pl
# erase-side branches (different transistor gate -> lower compliance)
phr = _logfit(hrs_model, Vhr, Ihr, [6e-10, 6.7])   # RESET-ret HRS
plr, _ = curve_fit(lrs_model, Vlr, Ilr, p0=[2e-6, 0.4, 0.05], maxfev=20000)
Gh_r, bh_r = phr
Isat_r, Vk_r, lam_r = plr

print("HRS (write) I=Is*sinh(aV):  Is=%.3e A  a=%.3f /V  R2_log=%.4f  R0=%.2e Ohm"
      % (Gh, bh, _r2(np.log(Ih), np.log(hrs_model(Vh, *ph))), 1 / (Gh * bh)))
print("HRS (erase) I=Is*sinh(aV):  Is=%.3e A  a=%.3f /V  R2_log=%.4f  R0=%.2e Ohm"
      % (Gh_r, bh_r, _r2(np.log(Ihr), np.log(hrs_model(Vhr, *phr))), 1 / (Gh_r * bh_r)))
print("LRS (write) tanh: Isat=%.3e A Vk=%.3f lam=%.3f  R2=%.4f  R_on=%.2e Ohm  Isat=%.1f uA"
      % (Isat, Vk, lam, _r2(Il, lrs_model(Vl, *pl)), Vk / Isat, Isat * 1e6))
print("LRS (erase) tanh: Isat=%.3e A Vk=%.3f lam=%.3f  R2=%.4f  R_on=%.2e Ohm  Isat=%.1f uA"
      % (Isat_r, Vk_r, lam_r, _r2(Ilr, lrs_model(Vlr, *plr)), Vk_r / Isat_r, Isat_r * 1e6))

# ---------- 2. generative single-cycle loop ----------
def simulate_cycle():
    Vset = rng.normal(1.30, 0.33)
    Vreset = rng.normal(-1.07, 0.26)
    Gh_c = Gh * np.exp(rng.normal(0, 0.516))      # lognormal HRS spread
    Isat_c = rng.normal(Isat, 0.01 * Isat)        # tight transistor clamp
    # SET sweep 0->5->0 (step 0.02)
    Vup = np.arange(0, 5.0001, 0.02)
    Vdn = Vup[::-1]
    set_state = 0  # 0=HRS,1=LRS
    Is_f = []
    for V in Vup:
        if set_state == 0 and V >= Vset:
            set_state = 1
        Is_f.append(lrs_model(V, Isat_c, Vk, lam) if set_state else hrs_model(V, Gh_c, bh))
    Is_r = [lrs_model(V, Isat_c, Vk, lam) for V in Vdn]   # stays LRS on return
    # RESET sweep 0->-1.7->0 (erase-side bias: lower-compliance LRS, same HRS physics)
    Gh_r_c = Gh_r * np.exp(rng.normal(0, 0.516))
    Isat_r_c = rng.normal(Isat_r, 0.05 * Isat_r)
    Vdn2 = np.arange(0, -1.7001, -0.02)
    Vup2 = Vdn2[::-1]
    rst_state = 1
    Ir_f = []
    for V in Vdn2:
        if rst_state == 1 and V <= Vreset:
            rst_state = 0
        Ir_f.append(hrs_model(V, Gh_r_c, bh_r) if rst_state == 0
                    else lrs_model(V, Isat_r_c, Vk_r, lam_r))
    Ir_r = [hrs_model(V, Gh_r_c, bh_r) for V in Vup2]      # stays HRS on return
    return (Vup, np.array(Is_f), Vdn, np.array(Is_r),
            Vdn2, np.array(Ir_f), Vup2, np.array(Ir_r), Vset, Vreset)


# ---------- 3. Monte-Carlo 53 cycles, overlay on data ----------
setc, rstc = load_all()
fig, ax = plt.subplots(1, 2, figsize=(13, 5.5))
# measured clouds
for c in setc.values():
    ax[0].semilogy(c["V"], np.abs(c["I"]), color="lightgrey", lw=0.6)
for c in rstc.values():
    ax[1].semilogy(c["V"], np.abs(c["I"]), color="lightgrey", lw=0.6)
# simulated
for _ in range(53):
    (Vup, Isf, Vdn, Isr, Vdn2, Irf, Vup2, Irr, *_ ) = simulate_cycle()
    ax[0].semilogy(Vup, np.abs(Isf), color="crimson", lw=0.4, alpha=0.5)
    ax[0].semilogy(Vdn, np.abs(Isr), color="orange", lw=0.4, alpha=0.5)
    ax[1].semilogy(Vdn2, np.abs(Irf), color="navy", lw=0.4, alpha=0.5)
    ax[1].semilogy(Vup2, np.abs(Irr), color="dodgerblue", lw=0.4, alpha=0.5)
ax[0].set_title("SET: grey=measured, red/orange=model"); ax[0].set_xlabel("V"); ax[0].set_ylabel("|I| (A)")
ax[0].set_ylim(1e-11, 1e-3)
ax[1].set_title("RESET: grey=measured, blue=model"); ax[1].set_xlabel("V"); ax[1].set_ylabel("|I| (A)")
ax[1].set_ylim(1e-12, 1e-4)
for a in ax: a.grid(True, which="both", alpha=0.2)
plt.tight_layout()
out = os.path.join(FIG, "05_model_vs_data.png")
plt.savefig(out, dpi=130)
print("saved", out)

# ---------- 4. quantitative agreement on median branches ----------
sim_set_lrs = lrs_model(Vl, Isat, Vk, lam)
print("\nAgreement (median LRS branch): MAPE=%.1f%%"
      % (np.mean(np.abs(sim_set_lrs - Il) / Il) * 100))
sim_hrs = hrs_model(Vh, Gh, bh)
print("Agreement (median HRS branch): MAPE(logI)=%.3f dec"
      % np.mean(np.abs(np.log10(sim_hrs) - np.log10(Ih))))
np.savez(os.path.join(HERE, "model_params.npz"),
         Gh=Gh, bh=bh, Isat=Isat, Vk=Vk, lam=lam)
