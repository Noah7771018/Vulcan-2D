"""VULCAN-2D core simulation engine.

Orchestrates: filament → transport → thermal → variability
over a voltage sweep, yielding I-V curves and state history.
"""

from __future__ import annotations
import time
import numpy as np
from models.filament import FilamentModel
from models.transport import TransportModel
from models.thermal import ThermalModel
from models.variability import VariabilityModel
from utils.helpers import voltage_sweep
from utils.constants import Q_E


class Simulator:
    """Top-level simulator that runs the memristor switching loop."""

    def __init__(self, params: dict):
        self.params = params
        self.variability = VariabilityModel(params)
        self._results: dict = {}

    def run(self) -> dict:
        """Execute the simulation and return results."""
        t0 = time.perf_counter()

        n_cycles = self.params.get("n_cycles", 1)
        all_cycles = []

        for cycle_idx in range(n_cycles):
            cycle_params = self.variability.perturb_cycle(self.params)
            cycle_result = self._run_one_cycle(cycle_params)
            all_cycles.append(cycle_result)

        elapsed = time.perf_counter() - t0

        self._results = {
            "cycles": all_cycles,
            "elapsed_s": elapsed,
        }
        self._compute_metrics()
        return self._results

    def _run_one_cycle(self, p: dict) -> dict:
        """Run a single voltage sweep cycle."""
        # Build voltage array
        v_max = p.get("v_max", 2.0)
        v_step = p.get("v_step", 0.02)
        v_sweep = voltage_sweep(v_max, v_step)

        # Initialize models
        filament = FilamentModel(p)
        transport = TransportModel(p)
        thermal = ThermalModel(p)

        dt_per_step = p.get("dt", 1e-6)  # Time per voltage step [s] (1 µs)

        # State variables
        r = 0.1e-9  # Initial filament radius [m]
        T = p.get("T_ambient", 300.0)
        r_max = p.get("r_max", 2.0e-9)

        # Storage
        i_arr = np.zeros_like(v_sweep)
        r_arr = np.zeros_like(v_sweep)
        T_arr = np.zeros_like(v_sweep)

        for idx, v in enumerate(v_sweep):
            ruptured = filament.is_ruptured(r)

            i_val = transport.compute_current(v, T, r, r_max, ruptured)

            # Apply compliance current
            icc = p.get("icc", 0.0)
            if icc > 0 and abs(i_val) > icc:
                i_val = np.sign(i_val) * icc

            T = thermal.temperature(v, i_val, T, dt_per_step)
            r = filament.step(v, T, r, dt_per_step)

            i_arr[idx] = i_val
            r_arr[idx] = r
            T_arr[idx] = T

        return {
            "v": v_sweep,
            "i": i_arr,
            "r": r_arr,
            "T": T_arr,
        }

    def _compute_metrics(self) -> None:
        """Extract key device metrics from simulation results."""
        cycles = self._results["cycles"]
        metrics_list = []

        for cycle in cycles:
            v, i = cycle["v"], cycle["i"]
            m = {}

            # Set voltage: positive sweep, where current jumps
            pos_mask = v > 0
            if pos_mask.any():
                v_pos = v[pos_mask]
                i_pos = abs(i[pos_mask])
                # Set voltage: find sharpest current increase in positive sweep
                if len(i_pos) > 3:
                    di_pos = np.diff(i_pos)
                    set_idx = np.argmax(di_pos)
                    m["v_set"] = v_pos[set_idx] if di_pos[set_idx] > 1e-9 else np.nan
                else:
                    m["v_set"] = np.nan

                # HRS resistance: first half of positive sweep (before set)
                set_idx = len(v_pos) // 3
                if set_idx > 2:
                    hrs_mask = slice(0, set_idx)
                    m["R_hrs"] = np.mean(np.abs(v_pos[hrs_mask] / (i_pos[hrs_mask] + 1e-15)))

                # LRS resistance: last quarter of positive sweep (after set)
                lrs_start = int(len(v_pos) * 0.7)
                if lrs_start < len(v_pos) - 2:
                    lrs_mask = slice(lrs_start, len(v_pos))
                    m["R_lrs"] = np.mean(np.abs(v_pos[lrs_mask] / (i_pos[lrs_mask] + 1e-15)))

            # Reset voltage: negative sweep, current drops from LRS to HRS
            neg_mask = v < 0
            if neg_mask.any():
                v_neg = v[neg_mask]
                i_neg_abs = abs(i[neg_mask])
                # Detect reset as maximum negative dI/dV point
                if len(i_neg_abs) > 3:
                    di = np.diff(i_neg_abs)
                    dv = np.diff(v_neg)
                    with np.errstate(divide="ignore", invalid="ignore"):
                        didv = np.abs(di / np.where(np.abs(dv) < 1e-12, 1e-12, dv))
                    # Find the largest negative di (reset transition)
                    reset_idx = np.argmax(-di)  # largest current drop
                    if di[reset_idx] < -1e-9:  # significant drop
                        m["v_reset"] = abs(v_neg[reset_idx])

            # On/Off ratio
            if "R_hrs" in m and "R_lrs" in m and m["R_lrs"] > 0:
                m["on_off_ratio"] = m["R_hrs"] / m["R_lrs"]

            # Max temperature
            m["T_max"] = float(np.max(cycle["T"]))

            metrics_list.append(m)

        self._results["metrics"] = metrics_list
