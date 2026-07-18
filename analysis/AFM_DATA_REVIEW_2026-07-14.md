# 溅射 h-BN CAFM 数据整理与模型含义

日期：2026-07-14

## 先说结论

这组数据说明的不是“看到了 4866 个硼空位”，而是：

> 在溅射 h-BN 的 CAFM 电流图中，分割出了 4866 个局部导电斑块；大多数斑块
> 的表观横向尺寸为几十纳米，说明电流在空间上明显不均匀，并集中在许多局部
> 区域。这为 VULCAN-2D 的“多个局部 patch 并联参与导电”提供了直接的材料级
> 证据。

CAFM 只能告诉我们“哪里更导电”，不能单独判断这些位置究竟是 Ag/Ti 离子、
硼空位、晶界，还是几种因素共同形成的路径。

## 1. 文件和测量条件

- 原始统计：`AFM/Conductive spot size distributions defect for sputter hBN.txt`
- 汇报文件：`AFM/Defect distribution.pptx`
- 样品示意：`Si/SiO2/W/h-BN/Ag/Ti`
- 溅射 h-BN 电流图：样品偏压 6 V，电流色标约 0--2.4 pA
- 全图：由 1 um 标尺推断为名义上的 `5 um x 5 um`
- 局部放大图：由 250 nm 标尺推断为约 `1 um x 1 um`
- 文献对照图：CVD h-BN，4.3 V，色标约 0--2 pA

txt 第一列是分割后导电斑块的投影面积 `A`，单位为 `m2`；第二列是落入该
面积区间的斑块数。为了便于理解，本文使用

```text
d_eq = 2 sqrt(A / pi)
```

把不规则斑块换算为“相同面积圆”的等效直径。它只是表观横向尺寸，不表示
斑块真的为圆形。

## 2. 统计结果

| 指标 | 结果 | 简单解释 |
|---|---:|---|
| 导电斑块总数 | 4866 | 图像分割出的连通区域数 |
| 面积众数/中位数 | 1759 nm2 | 超过一半落在最小的主要面积档 |
| 等效直径众数/中位数 | 47.3 nm | 最常见的表观斑块尺寸 |
| 平均等效直径 | 55.9 nm | 少量较大斑块把均值抬高 |
| 等效直径 P90 | 76.3 nm | 90% 的斑块不超过此尺寸 |
| 等效直径 P95 | 87.3 nm | 95% 的斑块不超过此尺寸 |
| 等效直径 P99 | 125.2 nm | 只有约 1% 更大 |
| 小于等于 100 nm 的比例 | 97.3% | 绝大多数是几十纳米级局部区域 |
| 所有斑块投影面积之和 | 13.09 um2 | 分割区域的面积总和 |
| 表观斑块密度 | 194.6 /um2 | 假定全图为 5 um x 5 um |
| 表观面积覆盖率 | 52.4% | 强烈依赖电流阈值和图像处理 |

分布图见
[11_afm_conductive_spot_distribution.png](figures/11_afm_conductive_spot_distribution.png)，
逐档数据见 [afm_spot_distribution.csv](afm_spot_distribution.csv)，机器可读摘要见
[afm_spot_summary.json](afm_spot_summary.json)。

## 3. 这组数据真正支持什么

### 支持 1：导电不是完全均匀的

电流图中存在许多局部导电区域，而且斑块尺寸分布很不均匀。换句话说，h-BN
不是每个位置都以相同方式导电，而是有很多“容易漏电或容易被激活的位置”。

### 支持 2：器件电流可以由许多局部路径相加

这与 VULCAN-2D 的并联 patch 表达一致：每个 patch 代表一组性质相近的局部
热点，端口总电流是这些区域电流的加和。不过模型权重不应只等于区域面积。
更完整的解释是 `w_k,eff proportional to A_k g_k`，其中 `A_k` 来自斑块
投影面积，`g_k` 汇总局部有效厚度、缺陷深度、势垒和电流幅值。Chen 等对
h-BN forming 也用 `I=J(t_eff)A` 说明缺陷面积和深度共同决定电流
[@Chen2020WaferScale]。

### 支持 3：局部路径处于纳米尺度，但不是原子缺陷本身

斑块等效直径主要为 47--90 nm，远大于一个硼空位或一条原子键。因此更合理
的解释是：一个 CAFM 斑块代表多个缺陷、晶界片段或金属辅助路径共同形成的
局部导电区域。文献报道的真正无序缺陷可以只有几个原子宽，但 CAFM 图像还会
受到探针半径、像素尺寸和阈值分割的横向展宽。Ranjan 等明确给出的 CAFM
空间分辨范围约为 10--100 nm，因此本数据 47.3 nm 的主要峰值很可能已经接近
测量/分割分辨尺度，不能解释为真实缺陷的横向直径[@Ranjan2018CAFM]。

### 支持 4：可以提出“缺陷引路、金属增强”的混合机制

溅射膜通常具有较多局部无序、空位和晶界；样品又含 Ag/Ti 活性金属。因此
可以提出：本征缺陷先提供低能路径，外加电场再激活局部导电，Ag/Ti 离子还
可能沿这些路径进入并增强电流。CAFM 支持“局部路径存在”，但金属是否真的
进入 h-BN 仍需 XTEM 配合 EDS/EELS 证明。

## 4. 目前不能直接下的结论

1. **不能把 4866 写成原子缺陷数。** 它是图像分割出的导电连通区域数。
2. **不能把 47 nm 写成硼空位直径。** 它是探针和图像处理共同影响后的表观
   斑块尺寸。
3. **不能仅凭这张图确定金属细丝。** Ag/Ti 迁移和硼空位桥都可能形成热点。
4. **不能严格声称比 CVD h-BN 的缺陷密度更高。** 两张图的偏压分别为 6 V
   和 4.3 V，扫描条件、阈值、探针及样品来源也不同。
5. **不能直接把模型的 `K` 改成 4866。** 若把当前表观密度仅作数量级外推，
   `194.6 /um2 x 0.053 um2` 约为 10.3，与 `K=10` 同量级；但样品和工艺不同，
   这只说明粗粒化阶数合理，不能解释为目标器件恰好有十根通道。`K=10` 仍是
   把大量真实斑块按阈值和贡献压缩成少量代表性亚群。

尤其需要注意：70.6% 的斑块都落在同一个最小主要面积档 `1759 nm2`。这很像
图像分割或像素尺寸造成的量化下限，说明小于约 47 nm 的真实分布可能没有被
充分分辨。

## 5. 对现有模型的处理决定

这批 CAFM 数据先作为**模型结构的独立支持**，暂不直接改动已由 53 轮 1T1R
电学数据标定的数值参数，原因是：

- CAFM 样品是溅射 h-BN，当前 1T1R 模型对应的是另一组器件；
- txt 只有斑块面积和数量，没有每个斑块的电流、开启电压和空间坐标；
- 几何面积不等于电流权重，一个小斑块也可能因为电导高而贡献很大；
- 仅在 6 V 下的一张图不能给出模型所需的阈值分布 `V_th,k`。

因此目前最稳妥的写法是：CAFM 验证“多局部路径和非均匀权重”这一模型框架，
而 txt 只约束 `A_k` 的空间几何分布，不直接给出局部导电因子 `g_k` 和开关
动力学。等拿到同一样品的原始 current matrix 和多偏压序列后，再用局部面积
与电流的乘积约束 `w_k`，用热点的开启顺序约束 `V_th,k`。

## 6. 可以放进论文的表述

> CAFM current mapping of sputtered h-BN at 6 V reveals a spatially
> heterogeneous ensemble of local conductive regions. Segmentation of the
> nominal 5 um x 5 um map yields 4866 apparent conductive spots, with a median
> equivalent circular diameter of 47.3 nm and 97.3% of spots below 100 nm.
> These apparent dimensions describe tip- and threshold-broadened conductive
> regions rather than individual atomic defects. The observation supports a
> coarse-grained parallel-patch description of distributed, spatially confined
> conduction, while the microscopic identity of each path remains to be
> resolved by cross-sectional microscopy and elemental analysis.

## 7. 文献对应关系

- Wen et al., *Advanced Materials* 33, 2100185 (2021) 报道 CVD 多层 h-BN 中
  少数原子宽的无序天然缺陷能够产生局部面外电流和随机电报噪声，支撑“二维
  晶体包围并限域局部导电缺陷”[@Wen2021Encryption]。
- Ranjan et al., *Scientific Reports* 8, 2854 (2018) 用 CAFM 在 h-BN 中观察到
  双极性和阈值型阻变，支撑局部路径能够发生开关和恢复[@Ranjan2018CAFM]。
- Xiao et al., *Advanced Functional Materials* 2017, 1700384 展示了 CAFM 如何
  区分局部突变导电和分布式电流变化；该文是氧化物器件，只能作为分析方法
  参照，不能直接证明 h-BN 机制[@Xiao2017CAFM]。

## 8. 下一步最有价值的数据

1. 原始 topography 与 current matrix，而不是只有 PPT 截图。
2. 图像分割使用的电流阈值、最小像素面积和去噪规则。
3. 同一区域从低偏压到高偏压的连续电流图，用来提取每个热点的开启电压。
4. 应力前后同一区域的配准图，判断热点是新增、扩大还是电流增强。
5. 同批样品多个位置的重复扫描，给出误差条而不是单张图统计。
6. 与 CAFM 区域对应的 XTEM/EDS/EELS，用来判断 Ag/Ti 是否沿缺陷进入 h-BN。

## 复现

```bash
python3 analysis/analyze_afm_spots.py
```

脚本默认按 PPT 标尺采用 `5 um x 5 um` 扫描范围；如果原始仪器元数据给出不同
范围，可用 `--scan-width-um` 和 `--scan-height-um` 重算密度与覆盖率。
