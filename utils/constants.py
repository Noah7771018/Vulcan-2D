"""Physical constants used across VULCAN-2D."""

# Fundamental constants
Q_E = 1.602176634e-19       # Elementary charge [C]
K_B = 1.380649e-23           # Boltzmann constant [J/K]
H_P = 6.62607015e-34         # Planck constant [J·s]
EPS0 = 8.854187817e-12       # Vacuum permittivity [F/m]
G0 = 2 * Q_E**2 / H_P        # Conductance quantum [S] ≈ 77.5 µS

# Material defaults (h-BN)
DEFAULT_EPS_R = 4.0          # Relative permittivity of h-BN
DEFAULT_THICKNESS = 5e-9     # Default h-BN thickness [m] (5 nm)
DEFAULT_GAP = 3.0 * Q_E      # Band gap energy [J] (~3 eV for h-BN)
DEFAULT_THERMAL_COND = 30.0  # Thermal conductivity [W/(m·K)] for h-BN
