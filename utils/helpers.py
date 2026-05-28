"""通用辅助函数。"""

from __future__ import annotations
import numpy as np


def smooth_step(x: np.ndarray, x0: float, width: float) -> np.ndarray:
    """S 形平滑阶跃 (sigmoid) 从 0 到 1。

    用于避免硬阈值切换导致的数值不连续。

    Args:
        x: 输入数组
        x0: 中心位置 (step 在 x=x0 处 = 0.5)
        width: 过渡宽度 (越小越陡)
    """
    return 1.0 / (1.0 + np.exp(-(x - x0) / width))


def voltage_sweep(v_max: float, v_step: float, n_cycles: int = 1) -> np.ndarray:
    """生成三角波电压扫描: 0 → +v_max → 0 → -v_max → 0。

    Args:
        v_max: 最大电压幅值 [V]
        v_step: 电压步长 [V]
        n_cycles: 完整扫描循环次数

    Returns:
        1D 电压数组，长度 = n_cycles × (4×ceil(v_max/v_step) + 1)
    """
    # 四段: 上升 → 下降 (越过零点) → 继续下降到负最大值 → 回升到 0
    half_up     = np.arange(0, v_max, v_step)
    half_down   = np.arange(v_max, -v_max, -v_step)
    half_return = np.arange(-v_max, 0 + v_step, v_step)

    one_cycle = np.concatenate([half_up, half_down, half_return])
    return np.tile(one_cycle, n_cycles)


def format_engineering(value: float, unit: str = "") -> str:
    """将数值格式化为工程计数法 (带前缀)。

    Example:
        1.5e-9  → "1.50 nΩ"
        3.2e6   → "3.20 MΩ"
    """
    if abs(value) < 1e-15:
        return f"0 {unit}"

    prefixes = {
        -12: "p", -9: "n", -6: "µ", -3: "m",
        0: "", 3: "k", 6: "M", 9: "G", 12: "T",
    }

    # 找到最近的 3 的倍数幂次
    exponent = int(np.floor(np.log10(abs(value)) / 3) * 3)
    exponent = max(-12, min(12, exponent))
    scaled = value / 10**exponent
    return f"{scaled:.2f} {prefixes[exponent]}{unit}"
