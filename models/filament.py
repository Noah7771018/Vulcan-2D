"""Conductive filament formation and rupture dynamics.

Threshold-switching model: filament radius evolves under voltage and temperature,
with distinct set (formation) and reset (rupture) transitions.
"""

from __future__ import annotations
import numpy as np
from utils.constants import Q_E, K_B


class FilamentModel:
    """Drives filament radius evolution via field- and temperature-assisted kinetics."""

    def __init__(self, params: dict):
        self.r_min = params.get("r_min", 0.05e-9)       # Minimum radius [m]
        self.r_max = params.get("r_max", 2.0e-9)        # Maximum radius [m]
        self.migration_barrier = params.get("migration_barrier", 0.6 * Q_E)  # [J]
        self.growth_rate_coeff = params.get("growth_rate_coeff", 1e-4)       # [m/s]
        self.dissolution_coeff = params.get("dissolution_coeff", 5e-4)       # [m/s]

    def growth_rate(self, v: float, T: float, r: float) -> float:
        """Compute dr/dt.

        Set (growth):  field lowers migration barrier → faster ion drift
            dr/dt ∝ exp(-(Ea - α|V|) / kT) * (1 - r/r_max)
        Reset (dissolution): thermal + reversed field breaks filament
            dr/dt ∝ -exp(-Ea/kT) * (r - r_min)/r_max  for V < -V_reset
        """
        if r <= self.r_min:
            r = self.r_min + 1e-12

        # Effective barrier lowered by electric field
        alpha = 2.0 * Q_E  # Barrier-lowering coefficient [J/V]
        E_eff = max(self.migration_barrier - alpha * abs(v), 0.05 * Q_E)
        ea_over_kt = E_eff / (K_B * T) if T > 0 else 50.0
        ea_over_kt = min(ea_over_kt, 80)

        boltzmann = np.exp(-ea_over_kt)

        if v > 0:
            # Positive bias: growth (set)
            growth = self.growth_rate_coeff * boltzmann * (1.0 - r / self.r_max)
            dissolution = 0.0
        else:
            # Negative bias: dissolution (reset)
            growth = 0.0
            dissolution = self.dissolution_coeff * boltzmann * r / self.r_max

        return growth - dissolution

    def step(self, v: float, T: float, r: float, dt: float) -> float:
        """Euler step forward in filament radius."""
        dr = self.growth_rate(v, T, r) * dt
        return np.clip(r + dr, self.r_min, self.r_max)

    def is_ruptured(self, r: float) -> bool:
        """Filament considered ruptured when near minimum radius."""
        return r <= 1.5 * self.r_min
