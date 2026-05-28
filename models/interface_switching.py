"""非细丝型界面切换模型 —— h-BN 1T1M 忆阻器 (Interface Switching).

基于 Nature 2023 (Zhu, Pazos et al.): h-BN 忆阻器的最优工作模式是
h-BN/电极界面处的离子交换，而非体内导电细丝。

核心物理图像:
  1. 内部状态变量 s ∈ [0,1] 表示界面离子交换位点的比例
     0 = 原始高阻态 HRS, 1 = 完全形成的低阻态 LRS
  2. s 的变化调制了金属/h-BN 界面的肖特基势垒高度
  3. 电流遵循修正的热电子发射公式
  4. 串联晶体管 (1T1M) 提供软电流顺应 (tanh 限流)

完整公式见 Obsidian: [[VULCAN-2D 拟合公式]]
"""

from __future__ import annotations
import numpy as np
from utils.constants import Q_E, K_B


class InterfaceSwitchingModel:
    """界面主导切换模型 —— 适用于 h-BN 1T1M 非细丝型忆阻器。

    10 个可调参数:
        phi_b0, phi_b_min: 原始/最小肖特基势垒 [J]
        n: 二极管理想因子
        I0: 电流缩放系数 [A]
        k_set, k_reset: Set/Reset 反应速率
        V_set_th, V_reset_th: Set/Reset 阈值电压 [V]
        k_switch: S 形开关陡峭度
        I_sat: 晶体管饱和电流 [A]
    """

    def __init__(self, params: dict):
        # ── 输运参数 ──
        self.phi_b0 = params.get("phi_b0", 0.7 * Q_E)      # 原始肖特基势垒 [J]
        self.phi_b_min = params.get("phi_b_min", 0.15 * Q_E) # 最小势垒 [J]
        self.ideality = params.get("ideality", 2.5)          # 二极管理想因子 n
        self.i0_scale = params.get("i0_scale", 1e-7)        # 电流缩放系数 [A]

        # ── 切换动力学参数 ──
        self.k_set = params.get("k_set", 0.5)              # Set 速率
        self.k_reset = params.get("k_reset", 2.0)          # Reset 速率
        self.v_set_th = params.get("v_set_th", 1.5)         # Set 阈值电压 [V]
        self.v_reset_th = params.get("v_reset_th", -0.5)    # Reset 阈值电压 [V]
        self.switch_slope = params.get("switch_slope", 10.0) # 开关陡峭度

        # ── 晶体管顺应参数 ──
        self.i_sat = params.get("i_sat", 5e-5)             # 晶体管饱和电流 [A]
        self.v_gate = params.get("v_gate", 1.1)            # 栅压 [V]

    # ══════════════════════════════════════════════════════════════
    # 势垒调制
    # ══════════════════════════════════════════════════════════════

    def barrier(self, s: float) -> float:
        """有效肖特基势垒高度 φ_B(s)。

        s=0 (HRS): φ_B = φ_B0       → 高势垒, 低电流
        s=1 (LRS): φ_B = φ_B_min   → 低势垒, 高电流
        """
        return self.phi_b0 - s * (self.phi_b0 - self.phi_b_min)

    # ══════════════════════════════════════════════════════════════
    # 电流输运
    # ══════════════════════════════════════════════════════════════

    def current(self, v: float, s: float, T: float = 300.0) -> float:
        """计算器件电流，含 1T1M 晶体管限流。

        分两步:
          1. 本征忆阻器电流 I_mem  (修正热电子发射)
          2. 晶体管软限流 I_final = I_sat * tanh(|I_mem|/I_sat)

        Args:
            v: 偏压 [V]
            s: 当前状态变量 (0=HRS ~ 1=LRS)
            T: 温度 [K]

        Returns:
            电流 [A]
        """
        phi_b = self.barrier(s)

        # ── 第 1 步: 本征忆阻器电流 ──
        if abs(v) < 1e-6:
            i_mem = 0.0  # 零偏压附近无电流
        else:
            if v > 0:
                # 正向: 热电子发射 I ∝ exp(-φ_B/kT) * [exp(qV/nkT)-1]
                i_mem = self.i0_scale * np.exp(-phi_b / (K_B * T)) * (
                    np.exp(abs(v) * Q_E / (self.ideality * K_B * T)) - 1
                )
            else:
                # 反向: 小欧姆电流 (势垒主导, 几乎无整流)
                i_mem = -self.i0_scale * np.exp(-phi_b / (K_B * T)) * abs(v)

        # ── 第 2 步: 晶体管软限流 ──
        # tanh(x) → x (x<<1): 不限制
        # tanh(x) → 1 (x>>1): 饱和到 I_sat
        i_transistor = self.i_sat * np.tanh(abs(i_mem) / self.i_sat)

        return np.sign(i_mem) * i_transistor if i_mem != 0 else 0.0

    # ══════════════════════════════════════════════════════════════
    # 状态演化
    # ══════════════════════════════════════════════════════════════

    def state_derivative(self, v: float, s: float) -> float:
        """计算 ds/dt —— 状态变量的瞬时变化率。

        正偏压 > V_set_th:    Set 项激活, 离子注入界面 → s↑
        负偏压 < V_reset_th:  Reset 项激活, 离子退回 → s↓

        两项均用 sigmoid 平滑开关, 避免数值突变。
        """
        # Set 驱动: sigmoid 在 V > V_set_th 时趋近 1
        set_drive = self.k_set * _sigmoid(v - self.v_set_th, self.switch_slope)

        # Reset 驱动: sigmoid 在 V < V_reset_th 时趋近 1
        reset_drive = self.k_reset * _sigmoid(self.v_reset_th - v, self.switch_slope)

        # ds/dt = 生长项*(1-s) - 消退项*s
        return set_drive * (1.0 - s) - reset_drive * s

    def step_state(self, v: float, s: float, dt: float) -> float:
        """Euler 前进一步, 更新状态变量 s。

        Args:
            v: 电压 [V]
            s: 当前状态值
            dt: 时间步长 [s]

        Returns:
            新的 s 值 (限幅在 [0, 1])
        """
        ds = self.state_derivative(v, s) * dt
        return np.clip(s + ds, 0.0, 1.0)


# ══════════════════════════════════════════════════════════════
# 辅助函数: 平滑 S 形开关
# ══════════════════════════════════════════════════════════════

def _sigmoid(x: float, k: float) -> float:
    """Sigmoid 函数: 1/(1+e^{-kx}), 带溢出保护。

    当 kx > 50:  ≈ 1
    当 kx < -50: ≈ 0
    """
    kx = k * x
    if kx > 50:
        return 1.0
    if kx < -50:
        return 0.0
    return 1.0 / (1.0 + np.exp(-kx))
