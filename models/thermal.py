"""Joule heating and simplified 1D thermal model."""

from __future__ import annotations
import numpy as np
from utils.constants import K_B


class ThermalModel:
    """Estimates filament temperature from Joule heating + heat dissipation."""

    def __init__(self, params: dict):
        self.T_ambient = params.get("T_ambient", 300.0)
        self.thermal_resistance = params.get("thermal_resistance", 1e4)  # [K/W]
        self.heat_capacity = params.get("heat_capacity", 1e-13)  # [J/K]
        self.tau_thermal = self.thermal_resistance * self.heat_capacity  # Time constant [s]

    def temperature(self, v: float, current: float, T_prev: float,
                    dt: float) -> float:
        """Compute temperature from Joule heating.

        dT/dt = (I*V - (T - T_ambient)/Rth) / Cth

        Uses an implicit-like relaxation: when dt >> tau, T → T_eq directly.
        """
        power = abs(v * current)
        T_eq = self.T_ambient + power * self.thermal_resistance

        if self.tau_thermal > 0:
            alpha = dt / self.tau_thermal
            if alpha > 10:
                T_new = T_eq  # Quasi-steady state
            else:
                T_new = T_prev + alpha * (T_eq - T_prev)
        else:
            T_new = T_eq

        return max(T_new, self.T_ambient)
