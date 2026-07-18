"""VULCAN-2D engine server exposing the calibrated v0.3 model to the UI.

A tiny stdlib HTTP server (no extra deps). GET /simulate runs an N-cycle Monte
Carlo of the calibrated model with optional UI parameter overrides and returns:
  * model SET / RESET median I-V loops (+ 10-90% bands),
  * the MEASURED median loops (from the xlsx) for the experiment<->simulation overlay,
  * the progressive phi_bar(V) trajectory (drives the distributed-path 3D view),
  * summary features (V_set, V_reset, R_HRS, R_LRS, I_cc, window) vs data targets.

Run:  <python-with-numpy/scipy/pandas> -m vulcan2d.serve   (default port 8000)
"""
import json
import os
import sys
from math import gamma, sqrt
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import numpy as np
from . import model as M
from . import features as F

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _res(*parts):
    """Resolve a bundled data file: PyInstaller (_MEIPASS/vulcan2d/...) or dev."""
    base = getattr(sys, "_MEIPASS", None)
    return os.path.join(base, "vulcan2d", *parts) if base else os.path.join(HERE, *parts)


CAL = _res("vulcan2d_calibrated.npz")
MEAS_JSON = _res("measured_loops.json")

# UI default for the single variability knob (keep in sync with the frontend)
SIGMA_UI_DEFAULT = 0.45
ICC_DEFAULT_UA = 51.0

_MEASURED = None  # cached measured loops (computed once)


def _downsample(x, n=240):
    x = np.asarray(x, float)
    if len(x) <= n:
        return x
    idx = np.linspace(0, len(x) - 1, n).astype(int)
    return x[idx]


def _branch_loop(cycles, key_V, key_I, n=240):
    """Per-index median + 10/90% band of |I| across cycles (shared waveform)."""
    V = np.asarray(cycles[0][key_V], float)
    A = np.array([np.abs(c[key_I]) for c in cycles])
    med = np.median(A, axis=0)
    lo = np.percentile(A, 10, axis=0)
    hi = np.percentile(A, 90, axis=0)
    return dict(V=_downsample(V, n).tolist(), med=_downsample(med, n).tolist(),
               lo=_downsample(lo, n).tolist(), hi=_downsample(hi, n).tolist())


def _measured_loops():
    """Measured median loops. Prefers the precomputed JSON (numpy-only, shipped
    in the packaged app); falls back to the xlsx in dev (needs pandas)."""
    global _MEASURED
    if _MEASURED is not None:
        return _MEASURED
    if os.path.exists(MEAS_JSON):
        with open(MEAS_JSON, encoding="utf-8") as f:
            _MEASURED = json.load(f)
        return _MEASURED
    # dev fallback (uncommon): build from the raw xlsx via the precompute helper
    from .precompute_measured import _loops
    _MEASURED = dict(
        setLoop=_loops(os.path.join(ROOT, "1T1M写入.xlsx")),
        resetLoop=_loops(os.path.join(ROOT, "1T1M擦除.xlsx")),
    )
    return _MEASURED


def _collect_features(cyc):
    """Per-cycle features WITHOUT pandas (so the shipped engine is numpy-only)."""
    keys = ["Vset", "Vreset", "R_HRS", "R_LRS", "Icc"]
    rows = []
    for c in cyc:
        f = F.set_feat(c["Vs"], c["Is"])
        f.update(F.reset_feat(c["Vr"], c["Ir"]))
        rows.append(f)
    return {k: np.array([r.get(k, np.nan) for r in rows], float) for k in keys}


def _scale_weibull_shape(shape, width_scale):
    """Return the Weibull shape whose CV is the baseline CV times width_scale."""
    def wcv(value):
        g1 = gamma(1.0 + 1.0 / value)
        return sqrt(gamma(1.0 + 2.0 / value) / (g1 * g1) - 1.0)

    target = wcv(shape) * max(width_scale, 0.0)
    if target < 1e-6:
        return 1e6
    lo, hi = 0.25, 1e4
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if wcv(mid) > target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _apply_overrides(p, q):
    def fval(name):
        v = q.get(name, [None])[0]
        return float(v) if v is not None else None

    icc = fval("icc_ua")
    if icc is not None:                       # compliance target -> scale transistor Isat
        p.Isat_set *= (icc * 1e-6) / (ICC_DEFAULT_UA * 1e-6)
    K = q.get("K", [None])[0]
    if K is not None:
        p.K = max(2, int(float(K)))
    sigma = fval("sigma")
    if sigma is not None:                     # one knob -> calibrated stochastic widths
        r = sigma / SIGMA_UI_DEFAULT
        p.sigma_lnG *= r
        p.sigma_Gon *= r
        p.sigma_theta *= r
        p.m_set = _scale_weibull_shape(p.m_set, r)
        p.m_reset = _scale_weibull_shape(p.m_reset, r)
    vset = fval("vset")
    if vset is not None:
        p.Vth_set0 = vset
    return p


def simulate(q):
    p = M.Params.from_npz(CAL)
    p = _apply_overrides(p, q)
    ncyc = int(float(q.get("ncycles", ["14"])[0]))
    seed = int(float(q.get("seed", ["110"])[0]))
    cyc, _ = M.simulate_cycles(p, n_cycles=ncyc, seed=seed)
    feat = _collect_features(cyc)

    half = len(cyc[0]["Vs"]) // 2
    phiV = _downsample(np.asarray(cyc[0]["Vs"], float)[:half + 1])
    phi = _downsample(np.asarray(cyc[0]["pbs"], float)[:half + 1])

    def stat(col):
        x = feat[col]
        x = x[np.isfinite(x)]
        return dict(mean=float(np.mean(x)), cv=float(np.std(x) / abs(np.mean(x)) * 100))

    feats = dict(
        Vset=stat("Vset"), Vreset=stat("Vreset"),
        R_HRS=stat("R_HRS"), R_LRS=stat("R_LRS"), Icc=stat("Icc"),
        window=float(np.nanmedian(feat["R_HRS"] / feat["R_LRS"])),
        phi_final=float(np.median([c["pbs"][len(c["Vs"]) // 2] for c in cyc])),
    )
    targets = dict(Vset=1.30, Vset_cv=25.0, Vreset=-1.07, Vreset_cv=24.0,
                   R_HRS=2.0e8, R_LRS=2.9e5, Icc=5.1e-5, window=668.0)
    meas = _measured_loops()
    return dict(
        setLoop=_branch_loop(cyc, "Vs", "Is"),
        resetLoop=_branch_loop(cyc, "Vr", "Ir"),
        measuredSet=meas["setLoop"], measuredReset=meas["resetLoop"],
        phiBar=dict(V=phiV.tolist(), phi=phi.tolist()),
        features=feats, targets=targets, K=int(p.K), ncycles=ncyc,
    )


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if body is not None:
            self.wfile.write(body if isinstance(body, bytes) else body.encode())

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/simulate":
            try:
                out = simulate(parse_qs(u.query))
                self._send(200, json.dumps(out))
            except Exception as e:  # noqa: BLE001
                import traceback
                traceback.print_exc()
                self._send(500, json.dumps({"error": str(e)}))
        elif u.path in ("/", "/health"):
            self._send(200, json.dumps({"ok": True, "engine": "vulcan2d v0.3"}))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, *a):  # quieter console
        pass


def main():
    port = int(os.environ.get("VULCAN_PORT", "8000"))
    print(f"VULCAN-2D engine on http://127.0.0.1:{port}  (warming measured data…)")
    _measured_loops()  # warm the xlsx cache up front
    print("ready.  GET /simulate")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
