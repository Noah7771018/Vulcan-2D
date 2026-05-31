"""Build-time step: precompute the measured median I-V loops from the two xlsx
files into vulcan2d/measured_loops.json, so the shipped engine needs only numpy
(no pandas/openpyxl, and no raw measurement data inside the distributed app).

Run once after the data changes:
    $VULCAN_PY -m vulcan2d.precompute_measured
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "measured_loops.json")


def _downsample(x, n=240):
    x = np.asarray(x, float)
    if len(x) <= n:
        return x
    return x[np.linspace(0, len(x) - 1, n).astype(int)]


def _loops(path, n=240, m=300):
    import pandas as pd
    xl = pd.ExcelFile(path)
    t = np.linspace(0, 1, m)
    Vs, Is = [], []
    for sn in xl.sheet_names:
        d = xl.parse(sn)
        V = d["voltage"].to_numpy(float)
        I = np.abs(d["current"].to_numpy(float))
        x = np.linspace(0, 1, len(V))
        Vs.append(np.interp(t, x, V))
        Is.append(np.interp(t, x, I))
    Vm = np.median(np.array(Vs), axis=0)
    Ia = np.array(Is)
    return dict(V=_downsample(Vm, n).tolist(),
               med=_downsample(np.median(Ia, axis=0), n).tolist(),
               lo=_downsample(np.percentile(Ia, 10, axis=0), n).tolist(),
               hi=_downsample(np.percentile(Ia, 90, axis=0), n).tolist())


def main():
    out = dict(
        setLoop=_loops(os.path.join(ROOT, "1T1M写入.xlsx")),
        resetLoop=_loops(os.path.join(ROOT, "1T1M擦除.xlsx")),
    )
    with open(OUT, "w") as f:
        json.dump(out, f)
    print("wrote", OUT, f"({len(out['setLoop']['V'])} pts/branch)")


if __name__ == "__main__":
    main()
