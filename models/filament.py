"""导电细丝形成与破裂动力学模型 (Conductive Filament Dynamics).

阈值切换模型：细丝半径在电场和温度驱动下演化，具有明确的
Set（形成）和 Reset（破裂）转变过程。

物理机制：
  - 正偏压 (V>0)：电场降低离子迁移势垒，加速氧空位/金属离子漂移 → 细丝生长
  - 负偏压 (V<0)：热效应 + 反向电场使细丝溶解断裂 → 细丝破裂
"""

from __future__ import annotations
import numpy as np
from utils.constants import Q_E, K_B


class FilamentModel:
    """细丝半径演化的场辅助动力学模型。

    核心方程:
      Set (V>0):  dr/dt = k_grow * exp(-(Ea - αV)/kT) * (1 - r/r_max)
      Reset (V<0): dr/dt = -k_diss * exp(-Ea/kT) * r/r_max

    参数:
        r_min: 细丝最小半径 [m]，破裂后残余 (默认 0.05 nm)
        r_max: 细丝最大半径 [m]，完全形成态 (默认 2 nm)
        migration_barrier: 离子迁移势垒 [J] (默认 0.6 eV)
        growth_rate_coeff: Set 生长速率系数 [m/s]
        dissolution_coeff: Reset 溶解速率系数 [m/s]
    """

    def __init__(self, params: dict):
        self.r_min = params.get("r_min", 0.05e-9)       # [m]
        self.r_max = params.get("r_max", 2.0e-9)        # [m]
        self.migration_barrier = params.get("migration_barrier", 0.6 * Q_E)  # [J]
        self.growth_rate_coeff = params.get("growth_rate_coeff", 1e-4)       # [m/s]
        self.dissolution_coeff = params.get("dissolution_coeff", 5e-4)       # [m/s]

    def growth_rate(self, v: float, T: float, r: float) -> float:
        """计算细丝半径变化率 dr/dt。

        Set (生长):  电场降低有效势垒 → exp(-(Ea-α|V|)/kT) * (1-r/r_max)
        Reset (溶解): 热 + 反向场 → -exp(-Ea/kT) * r/r_max

        Args:
            v: 瞬时电压 [V]
            T: 细丝温度 [K]
            r: 当前细丝半径 [m]
        """
        if r <= self.r_min:
            r = self.r_min + 1e-12  # 防止除零

        # α 系数：电场对势垒的降低效应，单位 J/V
        alpha = 2.0 * Q_E
        E_eff = max(self.migration_barrier - alpha * abs(v), 0.05 * Q_E)

        # Boltzmann 因子，限幅防止浮点溢出
        ea_over_kt = E_eff / (K_B * T) if T > 0 else 50.0
        ea_over_kt = min(ea_over_kt, 80)
        boltzmann = np.exp(-ea_over_kt)

        if v > 0:
            # 正偏压：生长主导
            growth = self.growth_rate_coeff * boltzmann * (1.0 - r / self.r_max)
            dissolution = 0.0
        else:
            # 负偏压：溶解主导
            growth = 0.0
            dissolution = self.dissolution_coeff * boltzmann * r / self.r_max

        return growth - dissolution

    def step(self, v: float, T: float, r: float, dt: float) -> float:
        """Euler 前进一步，更新细丝半径。

        Args:
            v: 电压 [V]
            T: 温度 [K]
            r: 当前半径 [m]
            dt: 时间步长 [s]
        """
        dr = self.growth_rate(v, T, r) * dt
        return np.clip(r + dr, self.r_min, self.r_max)

    def is_ruptured(self, r: float) -> bool:
        """判断细丝是否已断裂 (r 接近 r_min)。

        取 1.5×r_min 作为阈值，留出过渡带防止抖动。
        """
        return r <= 1.5 * self.r_min
