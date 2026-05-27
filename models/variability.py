"""Device variability model — cycle-to-cycle and device-to-device."""

from __future__ import annotations
import numpy as np
from utils.constants import Q_E

# Keys to perturb, with their default values (used for filling missing params)
_PERTURB_KEYS = {
    "migration_barrier": 0.6 * Q_E,
    "trap_depth": 0.4 * Q_E,
    "thermal_resistance": 1e4,
    "growth_rate_coeff": 1e-4,
    "dissolution_coeff": 5e-4,
    "r_min": 0.05e-9,
    "r_max": 2.0e-9,
}


class VariabilityModel:
    """Applies statistical perturbations to key device parameters."""

    def __init__(self, params: dict):
        self.enabled = params.get("variability_enabled", False)
        self.c2c_sigma = params.get("c2c_sigma", 0.05)
        self.d2d_sigma = params.get("d2d_sigma", 0.10)
        self._rng = np.random.default_rng(params.get("seed", 42))
        self._d2d_offsets: dict[str, float] = {}
        self._sample_d2d()

    def _sample_d2d(self) -> None:
        """Sample device-to-device offsets (once per device)."""
        for k in _PERTURB_KEYS:
            self._d2d_offsets[k] = self._rng.normal(0, self.d2d_sigma)

    def perturb_cycle(self, base_params: dict) -> dict:
        """Return a copy of base_params perturbed for one cycle.

        Perturbs parameters relevant to the filament and transport models,
        filling in defaults for any keys not present in base_params.
        """
        perturbed = dict(base_params)

        if not self.enabled:
            return perturbed

        float_keys = ["migration_barrier", "trap_depth", "thermal_resistance",
                      "growth_rate_coeff", "dissolution_coeff", "r_min", "r_max"]

        for k in float_keys:
            val = base_params.get(k, _PERTURB_KEYS.get(k, 0))
            c2c = self._rng.normal(0, self.c2c_sigma)
            d2d = self._d2d_offsets.get(k, 0.0)
            perturbed[k] = val * (1.0 + c2c + d2d)

        # Integer parameters
        qpc_default = 5
        if "qpc_channels" in base_params:
            qpc_val = base_params["qpc_channels"]
        else:
            qpc_val = qpc_default
        c2c_int = self._rng.integers(-1, 2)
        d2d_int = int(round(self._d2d_offsets.get("qpc_channels", 0) * 10))
        perturbed["qpc_channels"] = max(1, qpc_val + c2c_int + d2d_int)

        return perturbed
