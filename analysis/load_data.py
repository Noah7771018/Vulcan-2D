"""Load and structure the 1T1M h-BN memristor I–V data.

Two files, each 53 sheets (cycles):
  1T1M写入.xlsx  -> SET sweeps,   0 -> +5.0 V -> 0  (503 pts, step 0.02 V)
  1T1M擦除.xlsx  -> RESET sweeps, 0 -> -1.7 V -> 0  (173 pts, step 0.02 V)

Returns dicts keyed by cycle index (1..53) with arrays (V, I) split into
the up/forward and down/return half-sweeps.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WRITE = os.path.join(ROOT, "1T1M写入.xlsx")
ERASE = os.path.join(ROOT, "1T1M擦除.xlsx")


def _split_sweep(v):
    """Return index of the apex (max |v|) that separates forward/return."""
    return int(np.argmax(np.abs(v)))


def load_file(path):
    xl = pd.ExcelFile(path)
    cycles = {}
    for i, sn in enumerate(xl.sheet_names, start=1):
        df = xl.parse(sn)
        v = df["voltage"].to_numpy(float)
        cur = df["current"].to_numpy(float)
        m = np.isfinite(v) & np.isfinite(cur)
        v, cur = v[m], cur[m]
        apex = _split_sweep(v)
        cycles[i] = dict(
            sheet=sn, V=v, I=cur,
            V_fwd=v[: apex + 1], I_fwd=cur[: apex + 1],
            V_ret=v[apex:], I_ret=cur[apex:],
            apex=apex,
        )
    return cycles


def load_all():
    return load_file(WRITE), load_file(ERASE)


if __name__ == "__main__":
    setc, rstc = load_all()
    print(f"SET cycles: {len(setc)}, RESET cycles: {len(rstc)}")
    s = setc[1]
    print("SET S1: npts", len(s["V"]), "Vmax", s["V"].max(),
          "fwd", len(s["V_fwd"]), "ret", len(s["V_ret"]))
    r = rstc[1]
    print("RESET R1: npts", len(r["V"]), "Vmin", r["V"].min(),
          "fwd", len(r["V_fwd"]), "ret", len(r["V_ret"]))
