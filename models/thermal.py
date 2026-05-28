"""焦耳热模型 (Joule Heating & Thermal Dissipation).

简化版一维热模型：细丝区域的温度由焦耳热功率和散热决定。

物理方程:
    C_th * dT/dt = P_joule - (T - T_ambient) / R_th
    P_joule = |I * V|   (焦耳热功率)
"""

from __future__ import annotations
from utils.constants import K_B


class ThermalModel:
    """计算细丝区域的瞬时温度。

    参数:
        T_ambient: 环境温度 [K] (默认 300K)
        thermal_resistance: 热阻 [K/W] — 衡量散热能力，越小散热越快
        heat_capacity: 热容 [J/K] — 衡量升温惯性，越大温升越慢
        tau_thermal: 热时间常数 [s] = R_th * C_th
    """

    def __init__(self, params: dict):
        self.T_ambient = params.get("T_ambient", 300.0)
        self.thermal_resistance = params.get("thermal_resistance", 1e4)  # [K/W]
        self.heat_capacity = params.get("heat_capacity", 1e-13)  # [J/K]
        self.tau_thermal = self.thermal_resistance * self.heat_capacity  # [s]

    def temperature(self, v: float, current: float, T_prev: float,
                    dt: float) -> float:
        """前进一步，计算新温度。

        一阶 RC 热模型:
            dT/dt = (P_joule - (T - T_amb)/R_th) / C_th

        平衡温度: T_eq = T_amb + P_joule * R_th
        松弛:     T_new = T_old + (dt/tau) * (T_eq - T_old)

        Args:
            v: 瞬时电压 [V]
            current: 瞬时电流 [A]
            T_prev: 上一步温度 [K]
            dt: 时间步长 [s]
        """
        power = abs(v * current)  # 焦耳热 [W]

        # 平衡温度 = 环境温度 + 焦耳热 × 热阻
        T_eq = self.T_ambient + power * self.thermal_resistance

        if self.tau_thermal > 0:
            alpha = dt / self.tau_thermal  # 松弛因子
            if alpha > 10:
                # dt >> tau, 直接达到平衡态 (准稳态近似)
                T_new = T_eq
            else:
                # 一阶指数松弛
                T_new = T_prev + alpha * (T_eq - T_prev)
        else:
            T_new = T_eq

        return max(T_new, self.T_ambient)  # 温度不能低于环境温度
