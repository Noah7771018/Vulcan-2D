"""Bilingual string table for VULCAN-2D (中文 / English)."""

from __future__ import annotations
import streamlit as st

STRINGS = {
    "app_title": {
        "zh": "VULCAN-2D",
        "en": "VULCAN-2D",
    },
    "app_subtitle": {
        "zh": "二维材料忆阻器物理仿真器 — 面向层状材料导电分析的可变异性统一仿真器",
        "en": "2D Material Memristor Physical Simulator — Variability-aware Unified simulator for Layered-material Conduction ANalysis",
    },
    "welcome_about": {
        "zh": "### 关于",
        "en": "### About",
    },
    "welcome_desc": {
        "zh": (
            "VULCAN-2D 是一款面向**二维材料忆阻器**（h-BN、TMD 等）的物理仿真工具。\n\n"
            "它建模了以下物理过程：\n\n"
            "- **导电细丝**形成与破裂动力学\n"
            "- **电荷输运**（QPC 模型用于低阻态，Poole–Frenkel 用于高阻态）\n"
            "- **焦耳热**热效应\n"
            "- **器件变异性**（周期间与器件间）\n\n"
            "在侧边栏中调整参数，点击 **运行仿真** 即可开始。"
        ),
        "en": (
            "VULCAN-2D is a physics-based simulation tool for **2D material memristors** (h-BN, TMDs, etc.).\n\n"
            "It models:\n\n"
            "- **Conductive filament** formation & rupture dynamics\n"
            "- **Charge transport** (QPC model for LRS, Poole–Frenkel for HRS)\n"
            "- **Joule heating** thermal effects\n"
            "- **Device variability** (cycle-to-cycle & device-to-device)\n\n"
            "Adjust parameters in the sidebar and press **Run Simulation** to begin."
        ),
    },
    "welcome_device_structure": {
        "zh": "### 器件结构",
        "en": "### Device Structure",
    },
    "welcome_top_electrode": {
        "zh": "← 顶电极",
        "en": "← Top electrode",
    },
    "welcome_switching_layer": {
        "zh": "← 阻变层",
        "en": "← Switching layer",
    },
    "welcome_bottom_electrode": {
        "zh": "← 底电极",
        "en": "← Bottom electrode",
    },
    "welcome_hint": {
        "zh": "在左侧边栏中配置参数，然后点击 **运行仿真** 即可查看 I-V 曲线与器件指标。",
        "en": "Configure parameters in the left sidebar, then click **Run Simulation** to see I-V curves and device metrics.",
    },
    "run_button": {
        "zh": "运行仿真",
        "en": "Run Simulation",
    },
    "running": {
        "zh": "仿真运行中...",
        "en": "Running simulation...",
    },
    # ── Sidebar sections ──
    "sidebar_subtitle": {
        "zh": "面向层状材料导电分析的可变异性统一仿真器",
        "en": "Variability-aware Unified simulator for Layered-material Conduction ANalysis",
    },
    "section_device": {
        "zh": "器件结构",
        "en": "Device Structure",
    },
    "section_filament": {
        "zh": "细丝参数",
        "en": "Filament Parameters",
    },
    "section_electrical": {
        "zh": "电学条件",
        "en": "Electrical Setup",
    },
    "section_variability": {
        "zh": "变异性",
        "en": "Variability",
    },
    "section_thermal": {
        "zh": "热学设置",
        "en": "Thermal Settings",
    },
    "label_material": {
        "zh": "绝缘层材料",
        "en": "Insulator",
    },
    "label_thickness": {
        "zh": "厚度 [nm]",
        "en": "Thickness [nm]",
    },
    "label_eps_r": {
        "zh": "相对介电常数 εᵣ",
        "en": "Relative permittivity εᵣ",
    },
    "label_electrode": {
        "zh": "电极材料",
        "en": "Electrode",
    },
    "label_r_min": {
        "zh": "最小细丝半径 [nm]",
        "en": "Min filament radius [nm]",
    },
    "label_r_max": {
        "zh": "最大细丝半径 [nm]",
        "en": "Max filament radius [nm]",
    },
    "label_migration_barrier": {
        "zh": "迁移势垒 [eV]",
        "en": "Migration barrier [eV]",
    },
    "label_growth_rate": {
        "zh": "生长速率 [×10⁻⁴ m/s]",
        "en": "Growth rate [×10⁻⁴ m/s]",
    },
    "label_dissolution_rate": {
        "zh": "溶解速率 [×10⁻⁴ m/s]",
        "en": "Dissolution rate [×10⁻⁴ m/s]",
    },
    "label_qpc_channels": {
        "zh": "QPC 通道数",
        "en": "QPC channels",
    },
    "label_transmission": {
        "zh": "QPC 透射率",
        "en": "QPC transmission",
    },
    "label_trap_depth": {
        "zh": "陷阱深度 [eV]",
        "en": "Trap depth [eV]",
    },
    "label_v_max": {
        "zh": "电压扫描范围 [V]",
        "en": "Voltage sweep max [V]",
    },
    "label_v_step": {
        "zh": "电压步长 [mV]",
        "en": "Voltage step [mV]",
    },
    "label_icc": {
        "zh": "限流 [mA]（0 = 关闭）",
        "en": "Compliance current [mA] (0 = off)",
    },
    "label_n_cycles": {
        "zh": "扫描循环次数",
        "en": "Number of sweep cycles",
    },
    "label_T_ambient": {
        "zh": "环境温度 [K]",
        "en": "Ambient temperature [K]",
    },
    "label_variability_enabled": {
        "zh": "启用变异性",
        "en": "Enable variability",
    },
    "label_c2c_sigma": {
        "zh": "周期间 σ [%]",
        "en": "Cycle-to-cycle σ [%]",
    },
    "label_d2d_sigma": {
        "zh": "器件间 σ [%]",
        "en": "Device-to-device σ [%]",
    },
    "label_seed": {
        "zh": "随机种子",
        "en": "Random seed",
    },
    "label_thermal_resistance": {
        "zh": "热阻 [log10 K/W]",
        "en": "Thermal resistance [log10 K/W]",
    },
    "label_heat_capacity": {
        "zh": "热容 [log10 J/K]",
        "en": "Heat capacity [log10 J/K]",
    },
    # ── Material options ──
    "material_custom": {
        "zh": "自定义",
        "en": "Custom",
    },
    # ── Results ──
    "metric_v_set": {
        "zh": "V<sub>set</sub>",
        "en": "V<sub>set</sub>",
    },
    "metric_v_reset": {
        "zh": "V<sub>reset</sub>",
        "en": "V<sub>reset</sub>",
    },
    "metric_R_lrs": {
        "zh": "R<sub>LRS</sub>",
        "en": "R<sub>LRS</sub>",
    },
    "metric_R_hrs": {
        "zh": "R<sub>HRS</sub>",
        "en": "R<sub>HRS</sub>",
    },
    "metric_on_off": {
        "zh": "开关比",
        "en": "On/Off ratio",
    },
    "metric_T_max": {
        "zh": "最高细丝温度",
        "en": "Max filament temperature",
    },
    "metric_elapsed": {
        "zh": "仿真耗时",
        "en": "Simulation time",
    },
    # ── Tab titles ──
    "tab_temperature": {
        "zh": "温度分布",
        "en": "Temperature Profile",
    },
    "tab_filament": {
        "zh": "细丝演化",
        "en": "Filament Evolution",
    },
    "tab_variability": {
        "zh": "变异性分析",
        "en": "Variability Analysis",
    },
    # ── Plot titles ──
    "plot_iv_title": {
        "zh": "I–V 特性曲线",
        "en": "I–V Characteristic",
    },
    "plot_iv_cycle": {
        "zh": "循环",
        "en": "Cycle",
    },
    "plot_iv_curve": {
        "zh": "I-V 曲线",
        "en": "I-V Curve",
    },
    "plot_voltage": {
        "zh": "电压 [V]",
        "en": "Voltage [V]",
    },
    "plot_current": {
        "zh": "电流 [mA]",
        "en": "Current [mA]",
    },
    "plot_filament_title": {
        "zh": "细丝半径演化",
        "en": "Filament Radius Evolution",
    },
    "plot_filament_radius": {
        "zh": "半径 [nm]",
        "en": "Radius [nm]",
    },
    "plot_filament_label": {
        "zh": "细丝半径",
        "en": "Filament radius",
    },
    "plot_temperature_title": {
        "zh": "细丝温度",
        "en": "Filament Temperature",
    },
    "plot_temperature_label": {
        "zh": "温度 [K]",
        "en": "Temperature [K]",
    },
    "plot_temp_series": {
        "zh": "温度",
        "en": "Temperature",
    },
    "plot_variability_title": {
        "zh": "周期间变异性分布",
        "en": "Cycle-to-Cycle Variability",
    },
    "plot_variability_count": {
        "zh": "频次",
        "en": "Count",
    },
    "plot_variability_hint": {
        "zh": "需要 ≥2 个循环才能显示变异性分布",
        "en": "Need ≥2 cycles to show variability distribution",
    },
    # ── Raw data expander ──
    "raw_data": {
        "zh": "原始数据",
        "en": "Raw Data",
    },
    "raw_data_cycle": {
        "zh": "循环",
        "en": "Cycle",
    },
    "raw_data_points": {
        "zh": "个数据点",
        "en": "data points",
    },
    "raw_data_v_range": {
        "zh": "电压范围",
        "en": "V range",
    },
    "raw_data_i_range": {
        "zh": "电流范围",
        "en": "I range",
    },
    "raw_data_t_max": {
        "zh": "最高温度",
        "en": "T max",
    },
    "raw_data_r_range": {
        "zh": "半径范围",
        "en": "r range",
    },
    "variability_hint": {
        "zh": "请在侧边栏中增加扫描循环次数以查看变异性分析。",
        "en": "Increase number of sweep cycles in the sidebar to see variability analysis.",
    },
    # ── Language settings ──
    "lang_label": {
        "zh": "语言 / Language",
        "en": "语言 / Language",
    },
    "lang_setting_group": {
        "zh": "界面设置",
        "en": "Interface Settings",
    },
    # ── Experiment Data tab ──
    "exp_tab_title": {
        "zh": "实验数据分析",
        "en": "Experiment Data Analysis",
    },
    "exp_tab_caption": {
        "zh": "h-BN 1T1M 忆阻器 — Nature 2023 (Zhu, Pazos et al.)",
        "en": "h-BN 1T1M Memristor — Nature 2023 (Zhu, Pazos et al.)",
    },
    "exp_metric_set_cycles": {
        "zh": "Set 周期数",
        "en": "Set cycles",
    },
    "exp_metric_erase_cycles": {
        "zh": "Erase 周期数",
        "en": "Erase cycles",
    },
    "exp_metric_v_sweep": {
        "zh": "电压扫描",
        "en": "V sweep",
    },
    "exp_metric_i_range": {
        "zh": "电流范围 (Set)",
        "en": "I range (Set)",
    },
    "exp_metric_on_off": {
        "zh": "开关比",
        "en": "On/Off ratio",
    },
    "exp_metric_points": {
        "zh": "点/周期",
        "en": "Points/cycle",
    },
    "exp_tab_fitting": {
        "zh": "模型拟合",
        "en": "Model Fitting",
    },
    "exp_tab_heatmap": {
        "zh": "变异性热力图",
        "en": "Variability Heatmap",
    },
    "exp_tab_erase": {
        "zh": "擦除数据",
        "en": "Erase Data",
    },
    "exp_fitting_title": {
        "zh": "界面切换模型拟合",
        "en": "Interface-Switching Model Fit",
    },
    "exp_model_eq_title": {
        "zh": "模型公式",
        "en": "Model Equations",
    },
    "exp_state_var": {
        "zh": "**状态变量** $s \\in [0,1]$（0=HRS，1=LRS）：",
        "en": "**State variable** $s \\in [0,1]$ (0=HRS, 1=LRS):",
    },
    "exp_sigma_caption": {
        "zh": "其中 $\\sigma(x) = 1/(1+e^{-k \\cdot x})$",
        "en": "where $\\sigma(x) = 1/(1+e^{-k \\cdot x})$",
    },
    "exp_barrier_label": {
        "zh": "**势垒调制：**",
        "en": "**Barrier modulation:**",
    },
    "exp_current_label": {
        "zh": "**忆阻器电流**（热电子发射）：",
        "en": "**Memristor current** (thermionic emission):",
    },
    "exp_compliance_label": {
        "zh": "**晶体管限流**（1T1M 软饱和）：",
        "en": "**Transistor compliance** (1T1M soft limit):",
    },
    "exp_loss_label": {
        "zh": "**损失函数**（对数空间 MSE）：",
        "en": "**Loss function** (log-space MSE):",
    },
    "exp_params_label": {
        "zh": "10 个自由参数：$\\phi_{B0}, \\phi_{B,\\min}, n, I_0, k_{\\text{set}}, k_{\\text{reset}}, V_{\\text{set,th}}, V_{\\text{reset,th}}, k, I_{\\text{sat}}$",
        "en": "10 free parameters: $\\phi_{B0}, \\phi_{B,\\min}, n, I_0, k_{\\text{set}}, k_{\\text{reset}}, V_{\\text{set,th}}, V_{\\text{reset,th}}, k, I_{\\text{sat}}$",
    },
    "exp_run_fit_btn": {
        "zh": "运行拟合",
        "en": "Run Fit",
    },
    "exp_fitting_hint": {
        "zh": "点击 **运行拟合** 优化参数。",
        "en": "Click **Run Fit** to optimize parameters.",
    },
    "exp_fitted_params": {
        "zh": "**拟合参数：**",
        "en": "**Fitted Parameters:**",
    },
    "exp_fit_mse": {
        "zh": "MSE (log10)",
        "en": "MSE (log10)",
    },
    "exp_fit_time": {
        "zh": "拟合耗时",
        "en": "Fit time",
    },
    "exp_fit_running": {
        "zh": "正在拟合模型参数（约需 1-2 分钟）...",
        "en": "Fitting model parameters (this may take 1-2 minutes)...",
    },
    "exp_fit_waiting": {
        "zh": "点击 **运行拟合** 以用实验数据校准模型。",
        "en": "Press **Run Fit** to calibrate the model against experimental data.",
    },
    "exp_overview_title": {
        "zh": "实验 I-V：全部 Set 周期（h-BN 1T1M）",
        "en": "Experimental I-V: All Set Cycles (h-BN 1T1M)",
    },
    "exp_fit_compare_title": {
        "zh": "模型拟合 vs 实验",
        "en": "Model Fit vs Experiment",
    },
    "exp_mean_label": {
        "zh": "实验（均值）",
        "en": "Experiment (mean)",
    },
    "exp_model_label": {
        "zh": "模型（拟合）",
        "en": "Model (fitted)",
    },
    "exp_current_ua": {
        "zh": "电流 [µA]",
        "en": "Current [µA]",
    },
    "exp_heatmap_title": {
        "zh": "周期间变异性热力图（Set）",
        "en": "Cycle-to-Cycle Variability Heatmap (Set)",
    },
    "exp_heatmap_analysis": {
        "zh": """
        **变异性分析**：热力图展示了全部 53 个 Set 周期的对数电流变化。主要特征：
        - **HRS 区**（低电压）：变异性小，原始态稳定
        - **过渡区**（~1-3V）：变异性最大，开关起始点随机
        - **LRS 区**（高电压）：变异性中等，被顺应限流饱和
        """,
        "en": """
        **Variability Analysis**: The heatmap shows the log-scale current across
        all 53 set cycles. Key observations:
        - **HRS region** (low V): Low variability, stable pristine state
        - **Transition region** (~1-3V): Highest variability, stochastic switching onset
        - **LRS region** (high V): Moderate variability, compliance-limited saturation
        """,
    },
    "exp_erase_title": {
        "zh": "擦除（Reset）扫描 — 0 → -1.7V → 0",
        "en": "Erase (Reset) Sweeps — 0 → -1.7V → 0",
    },
    "exp_erase_plot_title": {
        "zh": "擦除 I-V：全部 Reset 周期（53 个）",
        "en": "Erase I-V: Reset Cycles (all 53)",
    },
    "exp_data_not_found": {
        "zh": "未找到实验数据于：",
        "en": "Experimental data not found at: ",
    },
    "exp_data_hint": {
        "zh": "请将 Nature h-BN 数据集文件（1T1M写入.xlsx, 1T1M擦除.xlsx）放入上述文件夹。",
        "en": "Place the Nature h-BN dataset files (1T1M写入.xlsx, 1T1M擦除.xlsx) in the folder above.",
    },
}


def t(key: str) -> str:
    """Return the translated string for the current language."""
    lang = st.session_state.get("lang", "zh")
    entry = STRINGS.get(key, {})
    return entry.get(lang, key)


def init_language() -> None:
    """Initialise language in session state if not set."""
    if "lang" not in st.session_state:
        st.session_state["lang"] = "zh"


def toggle_language() -> None:
    """Toggle between zh and en."""
    st.session_state["lang"] = "en" if st.session_state["lang"] == "zh" else "zh"
