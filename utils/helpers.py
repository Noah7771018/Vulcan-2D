"""General helper functions."""

from __future__ import annotations
import numpy as np


def smooth_step(x: np.ndarray, x0: float, width: float) -> np.ndarray:
    """Smooth sigmoid transition from 0 to 1 around x0 with given width."""
    return 1.0 / (1.0 + np.exp(-(x - x0) / width))


def voltage_sweep(v_max: float, v_step: float, n_cycles: int = 1) -> np.ndarray:
    """Generate a triangular voltage sweep: 0 -> +v_max -> 0 -> -v_max -> 0.

    Args:
        v_max: Maximum voltage magnitude [V].
        v_step: Voltage step size [V].
        n_cycles: Number of full sweep cycles.

    Returns:
        1D array of voltage values.
    """
    half_up = np.arange(0, v_max, v_step)
    half_down = np.arange(v_max, -v_max, -v_step)
    half_return = np.arange(-v_max, 0 + v_step, v_step)

    one_cycle = np.concatenate([half_up, half_down, half_return])
    return np.tile(one_cycle, n_cycles)


def format_engineering(value: float, unit: str = "") -> str:
    """Format a value with engineering prefixes."""
    if abs(value) < 1e-15:
        return f"0 {unit}"
    prefixes = {
        -12: "p", -9: "n", -6: "µ", -3: "m",
        0: "", 3: "k", 6: "M", 9: "G", 12: "T",
    }
    exponent = int(np.floor(np.log10(abs(value)) / 3) * 3)
    exponent = max(-12, min(12, exponent))
    scaled = value / 10**exponent
    return f"{scaled:.2f} {prefixes[exponent]}{unit}"
