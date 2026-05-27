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
