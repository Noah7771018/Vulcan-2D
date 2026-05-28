"""参数拟合引擎 —— 用实验数据校准模型参数 (Parameter Fitting).

两步优化策略:
  1. 差分演化 (Differential Evolution) —— 全局搜索，避免局部极值
  2. L-BFGS-B —— 局部精调，从 DE 最优解出发快速收敛

损失函数: 对数空间均方误差 (MSE in log10 space)
  L = mean( (log10|I_sim(V_i)| - log10|I_exp(V_i)|)² )

选对数空间的原因:
  忆阻器电流跨度 5-6 个数量级 (nA → µA)
  如果直接做线性 MSE，LRS 区域 (~µA) 会主导损失函数
  对数空间让 HRS (~nA) 和 LRS (~µA) 有相近权重
"""

from __future__ import annotations
import time
import numpy as np
from scipy.optimize import differential_evolution, minimize
from models.interface_switching import InterfaceSwitchingModel
from utils.constants import Q_E
from data.experiment_loader import ExperimentData


def run_interface_sweep(params: dict, v_sweep: np.ndarray) -> np.ndarray:
    """用界面切换模型跑一次电压扫描。

    从 s=0 (原始 HRS) 起步，随电压扫描演化状态变量。

    Args:
        params: 模型参数字典
        v_sweep: 电压扫描数组 [V]

    Returns:
        电流数组 [A]，长度与 v_sweep 相同
    """
    model = InterfaceSwitchingModel(params)
    dt = params.get("dt", 2e-6)           # 时间步长 [s]
    T = params.get("T_ambient", 300.0)    # 温度 [K]

    s = 0.0  # 从原始 HRS 态起步
    i_out = np.zeros_like(v_sweep)

    for idx, v in enumerate(v_sweep):
        i_out[idx] = model.current(v, s, T)     # 用当前状态计算电流
        s = model.step_state(v, s, dt)          # 根据电压更新状态

    return i_out


def compute_mse(i_sim: np.ndarray, i_exp: np.ndarray) -> float:
    """对数空间均方误差。

    取 log10 拉平 HRS (nA) 和 LRS (µA) 的权重。
    eps=1e-12 防止 log(0)。
    """
    eps = 1e-12
    log_sim = np.log10(np.abs(i_sim) + eps)
    log_exp = np.log10(np.abs(i_exp) + eps)
    return float(np.mean((log_sim - log_exp) ** 2))


def fit_interface_model(
    exp_data: ExperimentData,
    param_bounds: dict | None = None,
    seed: int = 42,
) -> dict:
    """用实验 I-V 数据拟合界面切换模型的 10 个参数。

    优化策略:
      Step 1: 差分演化 (DE) —— 全局搜索
        - 500 代 max，tol=1e-6
        - 不 polish，节省时间
      Step 2: L-BFGS-B —— 局部精调
        - 以 DE 最优解为起点
        - 1000 次迭代上限

    Args:
        exp_data: 实验 I-V 数据 (通常用 set_mean)
        param_bounds: 参数搜索范围 dict，None 则用默认值
        seed: 随机种子

    Returns:
        dict {
            'best_params':       最优参数值 (dict)
            'mse':               最终损失值 (log10 空间)
            'i_fitted':          用最优参数生成的拟合曲线 [A]
            'optimize_result':   scipy 优化结果对象
            'elapsed_s':         拟合耗时 [s]
        }
    """
    # —— 默认参数搜索范围 ——
    if param_bounds is None:
        param_bounds = {
            "phi_b0":      (0.3, 1.2),    # eV
            "phi_b_min":   (0.05, 0.4),   # eV
            "ideality":    (1.0, 5.0),
            "i0_scale":    (1e-9, 1e-4),  # A
            "k_set":       (0.1, 10.0),
            "k_reset":     (0.1, 20.0),
            "v_set_th":    (0.5, 3.0),    # V
            "v_reset_th":  (-1.5, 0.0),   # V
            "switch_slope":(2.0, 30.0),
            "i_sat":       (1e-6, 2e-4),  # A
        }

    # 将势垒类参数从 eV 转为 J
    bounds_j = {}
    for k, (lo, hi) in param_bounds.items():
        if k in ("phi_b0", "phi_b_min"):
            bounds_j[k] = (lo * Q_E, hi * Q_E)  # eV → J
        else:
            bounds_j[k] = (lo, hi)

    bounds_list = list(bounds_j.values())
    param_names = list(bounds_j.keys())
    v_sweep = exp_data.voltage   # 实验电压点
    i_exp = exp_data.current     # 实验电流点

    t0 = time.perf_counter()

    # —— 损失函数 ——
    def cost(x: np.ndarray) -> float:
        """x: 参数向量 (按 param_names 顺序排列)"""
        p = {name: val for name, val in zip(param_names, x)}
        p["dt"] = 2e-6
        p["T_ambient"] = 300.0
        try:
            i_sim = run_interface_sweep(p, v_sweep)
            return compute_mse(i_sim, i_exp)
        except Exception:
            return 1e10  # 数值异常时返回大损失，引导优化远离

    # —— Step 1: 差分演化全局搜索 ——
    result_de = differential_evolution(
        cost,
        bounds_list,
        seed=seed,
        maxiter=500,     # 最大代数
        tol=1e-6,         # 收敛容差
        polish=False,     # 不内建抛光，用 L-BFGS-B 替代
    )

    # —— Step 2: L-BFGS-B 局部精调 ——
    result_local = minimize(
        cost,
        result_de.x,          # 以 DE 最优解为起点
        method="L-BFGS-B",
        bounds=bounds_list,
        options={"maxiter": 1000},
    )

    # —— 组装结果 ——
    best_x = result_local.x
    best_params = {name: val for name, val in zip(param_names, best_x)}
    best_params["dt"] = 2e-6
    best_params["T_ambient"] = 300.0

    # 用最优参数生成拟合曲线
    i_fitted = run_interface_sweep(best_params, v_sweep)
    elapsed = time.perf_counter() - t0

    return {
        "best_params": best_params,
        "mse": float(result_local.fun),
        "i_fitted": i_fitted,
        "optimize_result": result_local,
        "elapsed_s": elapsed,
    }
