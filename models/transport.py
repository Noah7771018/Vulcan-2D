"""Charge transport model: QPC for LRS, Poole–Frenkel for HRS."""

from __future__ import annotations
import numpy as np
from utils.constants import Q_E, K_B, H_P, G0, EPS0


class TransportModel:
    """Selects and computes current based on filament/device state."""

    def __init__(self, params: dict):
        self.eps_r = params.get("eps_r", 4.0)
        self.thickness = params.get("thickness", 5e-9)  # [m]
        self.trap_depth = params.get("trap_depth", 0.4 * Q_E)  # [J]
        self.qpc_channels = params.get("qpc_channels", 5)
        self.transmission = params.get("transmission", 0.8)

    def current_qpc(self, v: float, r: float, r_max: float) -> float:
        """Quantum Point Contact current for low-resistance state.

        Conductance scales with filament cross-sectional area (r²/r_max²),
        modulated by voltage-dependent transmission probability.
        """
        ratio = max(r / r_max, 0.01)
        N_eff = self.qpc_channels * ratio ** 2
        V0 = 0.3  # Smoothing voltage [V]
        T_bar = self.transmission * np.tanh(abs(v) / V0)
        G = G0 * N_eff * T_bar
        return G * v

    def current_pf(self, v: float, T: float) -> float:
        """Poole–Frenkel conduction for high-resistance state."""
        E_field = abs(v) / self.thickness if self.thickness > 0 else 0

        # Barrier lowering
        beta = np.sqrt(Q_E**3 / (np.pi * self.eps_r * EPS0))
        barrier = self.trap_depth - beta * np.sqrt(E_field)
        barrier = max(barrier, 0.05 * Q_E)

        # Current ∝ E * exp(-barrier/kT)
        prefactor = 1e-2  # Scaling factor [A/V]
        if T > 0 and E_field > 0:
            current_density = prefactor * E_field * np.exp(-barrier / (K_B * T))
        else:
            current_density = 0.0

        area = 1e-14  # Effective area [m²]
        return current_density * area * np.sign(v)

    def compute_current(self, v: float, T: float, r: float, r_max: float,
                        is_ruptured: bool) -> float:
        """Pick QPC or PF based on filament state, with smooth transition."""
        eta = 1.0 if not is_ruptured else 0.0
        i_qpc = self.current_qpc(v, r, r_max)
        i_pf = self.current_pf(v, T)

        # Weighted blend for smooth LRS/HRS transition
        i_total = eta * i_qpc + (1 - eta) * i_pf

        # Enforce compliance current if provided
        return i_total
