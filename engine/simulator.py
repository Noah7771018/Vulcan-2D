"""VULCAN-2D 核心仿真引擎 (Simulation Engine).

将四个物理模块串联，在电压扫描下完成完整的忆阻器切换仿真:
  filament → transport → thermal → variability

每个电压点的计算流程:
  1. 判断细丝是否断裂 (filament.is_ruptured)
  2. 根据细丝状态计算电流 (transport.compute_current)
  3. 施加顺应限流 (compliance current, 如果启用)
  4. 更新温度 (thermal.temperature)
  5. 更新细丝半径 (filament.step)

输出: V 数组, I 数组, 以及细丝半径 r、温度 T 的演化历史。
"""

from __future__ import annotations
import time
import numpy as np
from models.filament import FilamentModel
from models.transport import TransportModel
from models.thermal import ThermalModel
from models.variability import VariabilityModel
from utils.helpers import voltage_sweep
from utils.constants import Q_E


class Simulator:
    """顶层仿真器 —— 串联各模块并执行仿真循环。

    使用方式:
        sim = Simulator(params)
        results = sim.run()
        # results['cycles']:  每个周期的 I-V-温度-半径数据
        # results['metrics']: 提取的关键指标 (V_set, V_reset, R_hrs, R_lrs, ...)
    """

    def __init__(self, params: dict):
        self.params = params
        self.variability = VariabilityModel(params)  # 变异性模块 (可开关)
        self._results: dict = {}

    # ══════════════════════════════════════════════════════════════
    # 主仿真循环
    # ══════════════════════════════════════════════════════════════

    def run(self) -> dict:
        """执行仿真并返回结果。

        流程:
          对每个电压扫描周期:
            1. 用变异性模型扰动参数
            2. 运行一个完整电压扫描
          收集所有周期后, 提取关键指标

        Returns:
            dict {
                'cycles':   [cycle_0_result, cycle_1_result, ...],
                'elapsed_s': 仿真耗时,
                'metrics':   每个周期的关键指标,
            }
        """
        t0 = time.perf_counter()

        n_cycles = self.params.get("n_cycles", 1)
        all_cycles = []

        for cycle_idx in range(n_cycles):
            # 变异性: 每个周期用扰动的参数重新仿真
            cycle_params = self.variability.perturb_cycle(self.params)
            cycle_result = self._run_one_cycle(cycle_params)
            all_cycles.append(cycle_result)

        elapsed = time.perf_counter() - t0

        self._results = {
            "cycles": all_cycles,
            "elapsed_s": elapsed,
        }
        self._compute_metrics()  # 自动提取 V_set, V_reset, HRS/LRS 等指标
        return self._results

    # ══════════════════════════════════════════════════════════════
    # 单周期扫描
    # ══════════════════════════════════════════════════════════════

    def _run_one_cycle(self, p: dict) -> dict:
        """运行一个完整的电压扫描周期。

        电压波形: 0 → +V_max → 0 → -V_max → 0 (三角波)
        每一步计算: 电流 → 限流 → 温度更新 → 细丝演化

        Returns:
            dict {
                'v': 电压数组 [V],
                'i': 电流数组 [A],
                'r': 细丝半径数组 [m],
                'T': 温度数组 [K],
            }
        """
        # —— 生成三角波电压扫描 ——
        v_max = p.get("v_max", 2.0)        # 最大电压 [V]
        v_step = p.get("v_step", 0.02)     # 电压步长 [V]
        v_sweep = voltage_sweep(v_max, v_step)

        # —— 初始化三个物理模块 ——
        filament = FilamentModel(p)
        transport = TransportModel(p)
        thermal = ThermalModel(p)

        dt_per_step = p.get("dt", 1e-6)     # 每步时间 [s]

        # —— 状态变量初值 ——
        r = 0.1e-9                          # 初始细丝半径 [m] (接近 r_min)
        T = p.get("T_ambient", 300.0)       # 初始温度 = 环境温度
        r_max = p.get("r_max", 2.0e-9)

        # —— 存储数组 ——
        i_arr = np.zeros_like(v_sweep)      # 电流
        r_arr = np.zeros_like(v_sweep)      # 细丝半径
        T_arr = np.zeros_like(v_sweep)      # 温度

        # —— 逐点扫描 ——
        for idx, v in enumerate(v_sweep):
            # 1. 判断细丝是否断裂
            ruptured = filament.is_ruptured(r)

            # 2. 根据状态选择导电机制 (QPC 或 P-F)
            i_val = transport.compute_current(v, T, r, r_max, ruptured)

            # 3. 顺应限流 (如果有设置 icc)
            icc = p.get("icc", 0.0)  # 0 = 不限流
            if icc > 0 and abs(i_val) > icc:
                i_val = np.sign(i_val) * icc

            # 4. 更新温度 (焦耳热)
            T = thermal.temperature(v, i_val, T, dt_per_step)

            # 5. 更新细丝半径 (场驱动生长/溶解)
            r = filament.step(v, T, r, dt_per_step)

            i_arr[idx] = i_val
            r_arr[idx] = r
            T_arr[idx] = T

        return {"v": v_sweep, "i": i_arr, "r": r_arr, "T": T_arr}

    # ══════════════════════════════════════════════════════════════
    # 指标提取
    # ══════════════════════════════════════════════════════════════

    def _compute_metrics(self) -> None:
        """从仿真结果中自动提取关键器件指标。

        提取内容:
          - V_set:   Set 电压 (正偏压扫描中电流突增点)
          - V_reset: Reset 电压 (负偏压扫描中电流骤降点)
          - R_hrs:   高阻态电阻 (扫描前半段低电压区)
          - R_lrs:   低阻态电阻 (扫描后半段高电压区)
          - on_off_ratio: 开关比 = R_hrs / R_lrs
          - T_max:   最高细丝温度
        """
        cycles = self._results["cycles"]
        metrics_list = []

        for cycle in cycles:
            v, i = cycle["v"], cycle["i"]
            m = {}

            # ── Set 电压 ──
            pos_mask = v > 0
            if pos_mask.any():
                v_pos = v[pos_mask]
                i_pos = abs(i[pos_mask])

                # Set 点: 正偏压下电流上升最快的电压点
                if len(i_pos) > 3:
                    di_pos = np.diff(i_pos)          # 电流差分
                    set_idx = np.argmax(di_pos)      # 最大上升点
                    m["v_set"] = v_pos[set_idx] if di_pos[set_idx] > 1e-9 else np.nan
                else:
                    m["v_set"] = np.nan

                # HRS 电阻: 正偏压前 1/3 段 (细丝未长成)
                set_idx = len(v_pos) // 3
                if set_idx > 2:
                    m["R_hrs"] = np.mean(np.abs(
                        v_pos[:set_idx] / (i_pos[:set_idx] + 1e-15)
                    ))

                # LRS 电阻: 正偏压后 30% (细丝已形成)
                lrs_start = int(len(v_pos) * 0.7)
                if lrs_start < len(v_pos) - 2:
                    m["R_lrs"] = np.mean(np.abs(
                        v_pos[lrs_start:] / (i_pos[lrs_start:] + 1e-15)
                    ))

            # ── Reset 电压 ──
            neg_mask = v < 0
            if neg_mask.any():
                v_neg = v[neg_mask]
                i_neg_abs = abs(i[neg_mask])
                if len(i_neg_abs) > 3:
                    di = np.diff(i_neg_abs)
                    reset_idx = np.argmax(-di)  # 最大电流下降点
                    if di[reset_idx] < -1e-9:
                        m["v_reset"] = abs(v_neg[reset_idx])

            # ── 开关比 ──
            if "R_hrs" in m and "R_lrs" in m and m["R_lrs"] > 0:
                m["on_off_ratio"] = m["R_hrs"] / m["R_lrs"]

            # ── 最高温度 ──
            m["T_max"] = float(np.max(cycle["T"]))

            metrics_list.append(m)

        self._results["metrics"] = metrics_list
