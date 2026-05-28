"""器件变异性模型 —— 周期间 (C2C) 与器件间 (D2D) (Device Variability).

对关键器件参数施加统计扰动，模拟真实忆阻器固有的随机性。

两种变异来源:
  - Cycle-to-Cycle (C2C): 每次电压扫描循环重新采样，模拟同一器件相邻循环的随机波动
  - Device-to-Device (D2D): 同一批次不同器件间的系统性偏移，初始化时采样一次后固定
"""

from __future__ import annotations
import numpy as np
from utils.constants import Q_E

# 需要扰动的参数及其默认值 (用于补全缺失参数)
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
    """对器件关键参数施加高斯扰动。

    参数:
        variability_enabled: 是否启用变异性 (默认关闭)
        c2c_sigma: 周期间高斯噪声标准差 (相对于参数值的比例)
        d2d_sigma: 器件间高斯噪声标准差
        seed: 随机种子 (可复现)
    """

    def __init__(self, params: dict):
        self.enabled = params.get("variability_enabled", False)
        self.c2c_sigma = params.get("c2c_sigma", 0.05)   # 默认 5%
        self.d2d_sigma = params.get("d2d_sigma", 0.10)   # 默认 10%
        self._rng = np.random.default_rng(params.get("seed", 42))
        self._d2d_offsets: dict[str, float] = {}

        # 初始化时采样一次 D2D 偏移 (模拟同一器件)
        self._sample_d2d()

    def _sample_d2d(self) -> None:
        """采样器件间偏移 (只执行一次)。"""
        for k in _PERTURB_KEYS:
            self._d2d_offsets[k] = self._rng.normal(0, self.d2d_sigma)

    def perturb_cycle(self, base_params: dict) -> dict:
        """返回经过周期扰动的参数副本。

        扰动方式: p' = p * (1 + C2C_noise + D2D_offset)
        其中 C2C_noise 每次调用重新采样，D2D_offset 固定不变。

        Args:
            base_params: 原始参数字典

        Returns:
            扰动后的参数副本 (不影响原字典)
        """
        perturbed = dict(base_params)  # 浅拷贝

        if not self.enabled:
            return perturbed

        # 浮点型连续参数: 乘性高斯噪声
        float_keys = ["migration_barrier", "trap_depth", "thermal_resistance",
                      "growth_rate_coeff", "dissolution_coeff", "r_min", "r_max"]

        for k in float_keys:
            val = base_params.get(k, _PERTURB_KEYS.get(k, 0))
            c2c = self._rng.normal(0, self.c2c_sigma)           # 每次重新采样
            d2d = self._d2d_offsets.get(k, 0.0)                 # 固定偏移
            perturbed[k] = val * (1.0 + c2c + d2d)

        # 整型参数: 加减整数偏移
        qpc_default = 5
        qpc_val = base_params.get("qpc_channels", qpc_default)
        c2c_int = self._rng.integers(-1, 2)                     # -1, 0, 或 +1
        d2d_int = int(round(self._d2d_offsets.get("qpc_channels", 0) * 10))
        perturbed["qpc_channels"] = max(1, qpc_val + c2c_int + d2d_int)

        return perturbed
