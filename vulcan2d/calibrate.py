"""Persist and audit the jointly calibrated VULCAN-2D v0.3 profile.

The electrical levels, stochastic widths, and endurance slopes are coupled.  A
naive sequence of one-parameter bisections can match each target temporarily and
then undo it when drift is enabled.  The Params defaults therefore hold the
joint profile obtained from a multi-seed coordinate search against all 53
measured cycles. This command reports the median and 10-90% interval across 12
independent 53-cycle C2C sequences and writes ``vulcan2d_calibrated.npz``.

Only quantities identifiable from the available quasi-static, single-device
data are active.  The thermal term remains disabled until variable-temperature
or pulse-width data are available.
"""
import os
import numpy as np
from . import model as M
from . import features as F

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT_SEEDS = tuple(range(100, 112))

TARGET = dict(
    Vset=1.298, Vset_cv=25.0,
    Vreset=-1.075, Vreset_cv=24.1,
    R_HRS=2.045e8, R_HRS_cv=45.5,
    R_LRS=2.939e5, R_LRS_cv=28.4,
    Icc=5.146e-5, Icc_cv=1.0,
    window=667.6,
    Vset_slope=8.524e-3,
    lnR_HRS_slope=-1.177e-2,
    lnR_LRS_slope=6.931e-3,
)


def slope(values, log=False):
    y = np.asarray(values, float)
    if log:
        y = np.log(np.clip(y, 1e-30, None))
    x = np.arange(len(y), dtype=float)
    ok = np.isfinite(y)
    return np.polyfit(x[ok], y[ok], 1)[0]


def cv(values):
    x = np.asarray(values, float)
    x = x[np.isfinite(x)]
    return np.std(x) / abs(np.mean(x)) * 100


def sequence_stats(p, seed):
    cycles, _ = M.simulate_cycles(p, n_cycles=53, seed=seed)
    df = F.extract_all(cycles)
    return dict(
        Vset_mean=np.mean(df.Vset), Vset_cv=cv(df.Vset),
        Vreset_mean=np.mean(df.Vreset), Vreset_cv=cv(df.Vreset),
        R_HRS_mean=np.mean(df.R_HRS), R_HRS_cv=cv(df.R_HRS),
        R_LRS_mean=np.mean(df.R_LRS), R_LRS_cv=cv(df.R_LRS),
        Icc_mean=np.mean(df.Icc), Icc_cv=cv(df.Icc),
        window=np.median(df.R_HRS / df.R_LRS),
        Vset_slope=slope(df.Vset),
        lnR_HRS_slope=slope(df.R_HRS, log=True),
        lnR_LRS_slope=slope(df.R_LRS, log=True),
    )


def audit(p, seeds=AUDIT_SEEDS):
    records = [sequence_stats(p, seed) for seed in seeds]
    return {key: np.array([record[key] for record in records], float)
            for key in records[0]}


def main():
    p = M.Params()
    result = audit(p)

    print("VULCAN-2D v0.3 multi-seed calibration audit")
    print("MODEL = median across 12 independent 53-cycle C2C sequences")
    print("-" * 80)
    print(f"{'feature':14s}{'MODEL median':>15s}{'MODEL CV':>10s} | "
          f"{'DATA mean':>13s}{'DATA CV':>9s}")
    rows = [
        ("V_set (V)", "Vset", TARGET["Vset"], TARGET["Vset_cv"]),
        ("V_reset (V)", "Vreset", TARGET["Vreset"], TARGET["Vreset_cv"]),
        ("R_HRS (Ohm)", "R_HRS", TARGET["R_HRS"], TARGET["R_HRS_cv"]),
        ("R_LRS (Ohm)", "R_LRS", TARGET["R_LRS"], TARGET["R_LRS_cv"]),
        ("I_cc (A)", "Icc", TARGET["Icc"], TARGET["Icc_cv"]),
    ]
    for name, key, target_mean, target_cv in rows:
        print(f"{name:14s}{np.median(result[key + '_mean']):>15.3e}"
              f"{np.median(result[key + '_cv']):>9.1f}% | "
              f"{target_mean:>13.3e}{target_cv:>8.1f}%")

    print(f"{'window':14s}{np.median(result['window']):>15.0f}{'':>10s} | "
          f"{TARGET['window']:>13.0f}")
    print("\nendurance slopes, median (model | data):")
    print(f"  V_set       {np.median(result['Vset_slope']):+.4g} | "
          f"{TARGET['Vset_slope']:+.4g} V/cycle")
    print(f"  ln R_HRS    {np.median(result['lnR_HRS_slope']):+.4g} | "
          f"{TARGET['lnR_HRS_slope']:+.4g} /cycle")
    print(f"  ln R_LRS    {np.median(result['lnR_LRS_slope']):+.4g} | "
          f"{TARGET['lnR_LRS_slope']:+.4g} /cycle")
    print("\n10-90% intervals of sequence-level means:")
    for key in ("Vset_mean", "Vreset_mean", "R_HRS_mean", "R_LRS_mean", "Icc_mean"):
        lo, hi = np.percentile(result[key], [10, 90])
        print(f"  {key:14s} [{lo:.4g}, {hi:.4g}]")
    print("\nthermal feedback: disabled (Rth=0; not identifiable from current data)")

    out = os.path.join(HERE, "vulcan2d_calibrated.npz")
    p.to_npz(out)
    print("saved", out)
    return p


if __name__ == "__main__":
    main()
