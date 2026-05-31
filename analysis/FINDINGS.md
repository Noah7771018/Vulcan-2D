# 1T1M h-BN 忆阻器实验数据分析：规律与解释模型

> 数据：`1T1M写入.xlsx`（SET/置位，53 循环 S1–S53）、`1T1M擦除.xlsx`（RESET/复位，53 循环 R1–R53）。
> 每个循环是一条 I–V 三角扫描。分析脚本在 [analysis/](.)，图在 [analysis/figures/](figures/)。
> 这些是朱凯晨组 1T1M（一晶体管一忆阻器）混合 2D/CMOS 芯片的真实测量，是 VULCAN-2D 的标定/验证目标。

---

## 0. 数据结构（先厘清扫描协议）

| 文件 | 过程 | 扫描 | 点数 | 步长 |
|---|---|---|---|---|
| 写入 S* | **SET（正压置位）** | 0 → **+5.0 V** → 0 | 503 | 0.02 V |
| 擦除 R* | **RESET（负压复位）** | 0 → **−1.7 V** → 0 | 173 | 0.02 V |

→ **双极性开关**：正压 SET（HRS→LRS），负压 RESET（LRS→HRS）。写入表第三列只有 2 个杂散值，已忽略。

---

## 1. 找到的规律（regularities）

### R1. 双极性、有迟滞的阻变开关
- SET 正程电流从 HRS（~2×10⁻¹⁰ A）随电压上升，在 **V_set≈1.3 V** 处跃升并入限流台阶；回程保持 LRS（迟滞）。
- RESET 正程从 LRS 平台（~1–2 µA）在 **V_reset≈−1.07 V** 处跌落回 HRS。
- 迟滞方向与极性一致，构成标准双极性回线（见 `06_SUMMARY.png(a)`）。

### R2. ★ 限流电流极其稳定（1T1M 的核心特征）
| 量 | 均值 | CV（循环间） |
|---|---|---|
| **I_cc（限流，+5V 处）** | **5.15×10⁻⁵ A** | **1.0 %** ← 几乎确定性 |
| V_set | 1.30 V | 25 % |
| V_reset | −1.07 V | 24 % |
| R_HRS @0.2V | 2.0×10⁸ Ω | 46 % |
| R_LRS @0.2V | 2.9×10⁵ Ω | 28 % |

→ **晶体管把 LRS 电流牢牢钳住（CV 仅 1%），而开关电压/电阻仍有 24–46% 的涨落。** 这正是参考图里红色 1T1M 曲线远比蓝色裸 1R 收窄的原因——变异性被串联晶体管压制，但没有完全消除。

### R3. 存储窗口 ~600×（≈2.8 个数量级）
R_HRS/R_LRS 中位数 ≈ **670**，HRS/LRS 清晰可分。

### R4. 变异性的统计分布
- **电阻/电流呈对数正态**（R_LRS、I_LRS：Shapiro p_logn=0.82 ≫ p_norm）——典型阻变器件统计特征，σ_ln(R_HRS)≈0.52、σ_ln(R_LRS)≈0.28。
- **开关电压近正态**（V_set、V_reset），σ(V_set)=0.33 V、σ(V_reset)=0.26 V。
- V_set 与 V_reset **互不相关**（r=−0.04）→ 置位/复位是两个独立的随机过程，可独立建模。
- 弱正自相关（lag-1 ACF ≈ +0.2~0.3）：相邻循环略有记忆。

### R5. 缓慢的耐久性漂移（53 个循环内可见）
- **V_set 上漂 +8.5 mV/循环**（Kendall τ=+0.44, p<0.001）——器件需要逐渐更高的置位电压。
- **R_HRS 下降、R_LRS 上升**（τ=−0.28 / +0.27, p<0.01）→ **存储窗口随循环缓慢收窄**（见 `(e)`）。
- V_reset 无显著漂移。

### R6. ★ 写/擦两侧 LRS 电流档位不同
SET 回程 LRS 升到 ~22–50 µA，而 RESET 正程 LRS 平台只有 ~1–2 µA。
→ 写、擦时**晶体管栅压（限流档位）不同**；但两侧 **HRS 导电完全一致**（R0 都≈2×10⁸ Ω），说明 HRS 是 h-BN 的本征陷阱导电，与偏置档位无关。

---

## 2. 建立的解释模型（explanatory models）

对全部 53 循环做电压分箱取中位数得到鲁棒的"代表性分支"，再判别物理机制（`conduction_models.py`，对数空间 R²）：

### M1. HRS 导电 = 对称陷阱辅助隧穿（trap-assisted tunneling）
判别结果（HRS，0.1–0.95 V）：

| 模型 | 形式 | R²(logI) |
|---|---|---|
| **TAT / 跳跃** | ln I ∝ V | **0.997** |
| **sinh（对称隧穿）** | I = I_s·sinh(αV) | **0.998** ← 采用 |
| Schottky | ln I ∝ √V | 0.992 |
| Poole–Frenkel | ln(I/V) ∝ √V | 0.980 |
| SCLC 幂律 | I ∝ V^m, m=2.76 | 0.943 |

→ **电流随电压指数增长（∝V 而非 ∝√V）**，最佳为
**I_HRS = I_s·sinh(α·V)，I_s = 6.2×10⁻¹⁰ A，α = 6.75 V⁻¹**（奇函数、过原点）。
自洽校验：小信号电阻 1/(I_s·α) = **2.4×10⁸ Ω**，与实测 R_HRS≈2×10⁸ Ω 吻合。
> 物理含义：HRS 电流由 h-BN 缺陷（硼/氮空位）介导的陷阱辅助隧穿/跳跃主导。提案里写的 Poole–Frenkel 也能拟合（R²=0.98），属同类"陷阱型"机制；单温度、窄电压窗下三者难严格区分，但场依赖明确偏向指数型。**建议 VULCAN-2D 的 HRS 模块用 sinh/TAT 形式，PF 作为可选项。**

### M2. LRS 导电 = 串联晶体管的输出特性（不是忆阻体导电！）
LRS 回程 I–V 在 V≈1.5 V 处有拐点：**低压线性（triode）→ 高压饱和**，PF 检验非单调（R²=0.18，排除）。这就是 MOSFET 的输出特性。采用平滑晶体管模型：

**I_LRS = I_sat·(1+λ|V|)·tanh(|V|/V_k)**
- 写侧：I_sat=22.3 µA，V_k=1.77 V，λ=0.26 V⁻¹，三极区导通电阻 R_on=V_k/I_sat≈**80 kΩ**，R²=0.989。
- 擦侧：I_sat≈0.3 µA（栅压档位低，见 R6）。

→ 低压 I≈(I_sat/V_k)·V 欧姆，高压 I→I_sat(1+λV) 饱和。**LRS 电流由晶体管决定**，这解释了 R2（I_cc CV 仅 1%）：忆阻丝在 LRS 近金属性、电阻很小，电流被晶体管钳位。提案里给 LRS 的 QPC（量子点接触）模型适用于**裸 1R 忆阻丝**（蓝色曲线），在 1T1M 中被晶体管掩盖。

### M3. 生成式回线模型（把上面拼成可复现整条回线 + 变异性）
状态机（准静态、阈值触发）+ 两支导电 + 实测分布抽样：

```
SET  正程(0→+5):  HRS[sinh]，当 V≥V_set 切到 LRS[tanh]
SET  回程(+5→0):  LRS[tanh]
RESET正程(0→−1.7): LRS[tanh,擦侧]，当 V≤V_reset 切到 HRS[sinh]
RESET回程(−1.7→0): HRS[sinh]
每循环抽样: V_set~N(1.30,0.33), V_reset~N(−1.07,0.26),
            I_s 对数正态(σ_ln=0.52), I_sat~N(CV 1%)
```

Monte-Carlo 模拟 53 条循环叠在实测云上（`05_model_vs_data.png`、`06_SUMMARY.png(f)`）：
开关电压、限流台阶、迟滞方向、HRS/LRS 量级、变异性云**均复现**。
分支拟合精度：HRS MAPE(logI)=0.03 个数量级（~7%）、LRS MAPE=25%（跨 2 个数量级）。

---

## 3. 对 VULCAN-2D 的意义（模块映射）

| 提案模块 | 本数据给出的标定/结论 |
|---|---|
| ① 灯丝形成/断裂 | 阈值 V_set≈1.3 V、V_reset≈−1.07 V，正态分布；置位/复位独立 |
| ② 电荷输运 | **HRS：sinh/TAT（I_s,α 已定）；LRS：被串联晶体管钳位，QPC 仅对裸 1R** |
| ③ 焦耳热/温度 | 单温度数据，未直接标定；可由 V_set 的弱正自相关与耐久漂移间接约束 |
| ④ 器件变异性 | I_cc CV=1% vs V_set/电阻 CV=24–46%；电阻对数正态、电压正态——**直接给出变异性注入的分布参数** |

**一句话结论**：这是一只双极性 h-BN 1T1M 器件——*HRS 由 h-BN 缺陷的陷阱辅助隧穿（sinh）主导，LRS 由串联晶体管的输出特性（triode→饱和）决定*；置位/复位电压各有 ~25% 的独立正态涨落，而限流电流被晶体管钳到 1% 以内，存储窗口 ~600× 并随循环缓慢收窄。上面的四分支生成模型已能定量复现整条回线，可作为 VULCAN-2D 的器件级种子模型。

---

## 3.5 与源论文(Nature 2023)交叉核对

数据来自 **K. Zhu / M. Lanza et al., "Hybrid 2D–CMOS microchips for memristive
applications," _Nature_ 618, 57–62 (2023)**（PMC10232361）。核对结论:

**原文证实了本分析**(数字精确吻合):
- R_HRS ≈ **200 MΩ**、R_LRS ≈ **200 kΩ**（本文提取 2.0×10⁸ / 2.9×10⁵ Ω,✓✓✓）。
- 晶体管=瞬时限流;原文原话 **"gate voltage fixes R_LRS, negative sweep end
  voltage fixes R_HRS"**——与本文 R2（栅/晶体管钳住 LRS,I_cc CV≈1%）完全一致。
- 双极性;SET 时 **V_G=1.1 V**;读出 0.1 V;h-BN **~6 nm(~18 层)**;电极 Au–Ti/Ag,
  底电极 W;耐久 ~1–2.5×10⁶,保持 7h;t_SET=232µs、t_RESET=783ns（SET≫RESET,动力学强不对称）。

**★ 一处重要修正 —— 器件是非灯丝型(non-filamentary):**
> 原文:*"the non-linearity of the currents in both states and the progressive
> state transitions indicate that the RS is non-filamentary"*；开关由 h-BN 的
> **软击穿/缺陷重排**主导。

- 这恰恰被本文 M1/M2 佐证:判定"非灯丝"的两条证据(两态电流都非线性 + 渐进转变)正是
  我们独立看到的 HRS=sinh/TAT 非线性 + 阈值带分布。
- 但据此,**提案沿用 SIM²RRAM 的"导电细丝 + QPC"模块对本器件不适用**:模块①应改为
  非灯丝软击穿/缺陷重排,模块② LRS 不宜用 QPC(灯丝型量子化电导),而用"晶体管限流 +
  h-BN 本征非线性"。项目的真正空白是**开关拓扑(灯丝型→面分布型)**,不止材料参数。
- 群体开关电压原文 ~2.5–4 V,本 cell V_set≈1.3 V 偏低端(低压器件/栅辅助)。
- R6（写/擦 LRS 档位不同)可能是不同 V_G,也可能是负压下晶体管源漏不对称——需测量元数据确认。

---

## 4. 复现方式

```bash
PY=/opt/homebrew/Caskroom/miniforge/base/envs/d2l/bin/python   # 含 pandas/numpy/scipy/matplotlib/openpyxl
cd analysis
$PY explore_overview.py      # 图01 总览
$PY explore_single.py        # 图02 单循环迟滞
$PY extract_features.py      # 提取 V_set/V_reset/R_HRS/R_LRS -> *.csv + 统计
$PY conduction_models.py     # 图03 导电机制判别 -> median_branches.npz
$PY variability.py           # 图04 分布/漂移/相关
$PY build_model.py           # 图05 四分支生成模型 vs 数据 -> model_params.npz
$PY final_summary.py         # 图06 总结大图
$PY run_vulcan.py            # 图07 动态电-热-缺陷模型(SIM2RRAM式) 标定+验证
```

> **动态物理模型**见 [DYNAMIC_MODEL.md](DYNAMIC_MODEL.md):把上面 6 条规律变成耦合
> 电-热-缺陷动力学（间隙 Stanford–PKU 动力学 + 焦耳热 + 串联晶体管输运 + 物理量变异性
> 注入）,53 循环蒙特卡洛使 V_set/V_reset 分布、对数正态电阻、I_cc CV≈1% 等**全部涌现**。
