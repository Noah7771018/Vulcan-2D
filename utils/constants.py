"""VULCAN-2D 物理常数与材料默认参数。

所有常数使用 SI 单位。
"""

# ── 基本物理常数 ──
Q_E   = 1.602176634e-19    # 基本电荷 [C]
K_B   = 1.380649e-23        # 玻尔兹曼常数 [J/K]
H_P   = 6.62607015e-34      # 普朗克常数 [J·s]
EPS0  = 8.854187817e-12     # 真空介电常数 [F/m]

# ── 导出常数 ──
G0    = 2 * Q_E**2 / H_P    # 电导量子 ≈ 77.5 µS (Landauer 公式)

# ── h-BN 默认材料参数 ──
DEFAULT_EPS_R       = 4.0            # 相对介电常数 (h-BN 面外)
DEFAULT_THICKNESS   = 5e-9           # 默认 h-BN 厚度 [m] (5 nm)
DEFAULT_GAP         = 3.0 * Q_E      # h-BN 带隙 [J] (~3 eV)
DEFAULT_THERMAL_COND = 30.0          # h-BN 热导率 [W/(m·K)]
