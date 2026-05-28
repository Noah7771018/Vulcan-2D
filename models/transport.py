"""电荷输运模型：低阻态 QPC + 高阻态 Poole-Frenkel (Charge Transport).

根据细丝状态自动切换导电机制：
  - 细丝连通 (LRS): 量子点接触 (QPC) 弹道输运
  - 细丝断裂 (HRS): Poole-Frenkel 陷阱辅助热发射

参考资料:
  - QPC: Long et al., Sci. Rep. 3, 2929 (2013)
  - P-F: 见 Obsidian 笔记 "VULCAN-2D 忆阻器导电机理综述"
"""

from __future__ import annotations
import numpy as np
from utils.constants import Q_E, K_B, G0, EPS0


# ──────────────────────────────────────────────────────────────────
# QPC (Quantum Point Contact) 模型 —— 低阻态
#
# 导电机理：细丝最窄处形成原子尺度的收缩区，电子弹道输运
#          电导被量子化为 G0 的整数倍
#          G = G0 * N_eff * T(E)
# 其中:
#   G0 = 2e²/h ≈ 77.5 µS   (电导量子)
#   N_eff: 有效导电通道数 ∝ (r/r_max)²
#   T(E):  电压相关的透射概率
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# Poole-Frenkel 发射 —— 高阻态
#
# 导电机理：绝缘层内陷阱中的电子被电场降低势垒后热激发到导带
#          J ∝ E * exp(-q(φ_B - Δφ)/kT)
#          其中 Δφ = sqrt(qE / π ε_i ε_0)
# ──────────────────────────────────────────────────────────────────


class TransportModel:
    """根据细丝状态选择 QPC (LRS) 或 Poole-Frenkel (HRS) 计算电流。

    参数:
        eps_r: 绝缘层相对介电常数 (h-BN 默认 4.0)
        thickness: 绝缘层厚度 [m] (默认 5 nm)
        trap_depth: P-F 陷阱深度 [J] (默认 0.4 eV)
        qpc_channels: QPC 最大导电通道数
        transmission: QPC 最大透射概率
    """

    def __init__(self, params: dict):
        self.eps_r = params.get("eps_r", 4.0)
        self.thickness = params.get("thickness", 5e-9)
        self.trap_depth = params.get("trap_depth", 0.4 * Q_E)
        self.qpc_channels = params.get("qpc_channels", 5)
        self.transmission = params.get("transmission", 0.8)

    def current_qpc(self, v: float, r: float, r_max: float) -> float:
        """QPC 电流 —— 用于 LRS。

        导电通道数 N_eff ∝ (r/r_max)²，即与细丝横截面积成正比。
        透射概率用 tanh 平滑地从 0 过渡到 T_max。

        返回: 电流 [A]
        """
        ratio = max(r / r_max, 0.01)  # 避免 r=0 导致零通道
        N_eff = self.qpc_channels * ratio ** 2

        V0 = 0.3  # 平滑电压 [V]
        T_bar = self.transmission * np.tanh(abs(v) / V0)

        # 总电导 = 量子电导 × 通道数 × 透射率
        G = G0 * N_eff * T_bar
        return G * v

    def current_pf(self, v: float, T: float) -> float:
        """Poole-Frenkel 电流 —— 用于 HRS。

        通过电场辅助的陷阱热发射导电机理。
        电压越高 → 电场越强 → 陷阱势垒被降低越多 → 电流指数增大。

        返回: 电流 [A]
        """
        # 电场强度 [V/m]
        E_field = abs(v) / self.thickness if self.thickness > 0 else 0

        # P-F 系数 β = sqrt(q³ / π εᵢ ε₀)
        beta = np.sqrt(Q_E**3 / (np.pi * self.eps_r * EPS0))

        # 有效势垒 = 原始陷阱深度 - 电场降低量
        barrier = self.trap_depth - beta * np.sqrt(E_field)
        barrier = max(barrier, 0.05 * Q_E)  # 势垒不能降到零

        # J ∝ E * exp(-barrier/kT) —— 体效应，面积为传导致横截面积
        prefactor = 1e-2  # 缩放系数 [A/V]
        if T > 0 and E_field > 0:
            current_density = prefactor * E_field * np.exp(-barrier / (K_B * T))
        else:
            current_density = 0.0

        area = 1e-14  # 有效导电面积 [m²]
        return current_density * area * np.sign(v)

    def compute_current(self, v: float, T: float, r: float, r_max: float,
                        is_ruptured: bool) -> float:
        """根据细丝断裂状态，用加权混合返回总电流。

        - 细丝连通 (not ruptured): eta=1, 纯 QPC 导电
        - 细丝断裂 (ruptured):     eta=0, 纯 P-F 导电
        过渡带可实现平滑切换。

        返回: 总电流 [A]
        """
        eta = 1.0 if not is_ruptured else 0.0  # 权重因子

        i_qpc = self.current_qpc(v, r, r_max)
        i_pf = self.current_pf(v, T)

        # 加权混合：LRS 由 QPC 主导，HRS 由 P-F 主导
        i_total = eta * i_qpc + (1 - eta) * i_pf
        return i_total
