"""VULCAN-2D — Streamlit app entry point.

面向二维材料忆阻器的多尺度物理建模与仿真器
Variability-aware Unified simulator for Layered-material Conduction ANalysis

架构概览:
  app.py                  主入口 —— 页面布局、标签页路由
  ├── models/             物理模型层
  │   ├── filament.py     细丝动力学 (Conductive Filament)
  │   ├── transport.py    电荷输运 (QPC + Poole-Frenkel)
  │   ├── thermal.py      焦耳热模型
  │   ├── variability.py  器件变异性 (C2C & D2D)
  │   └── interface_switching.py  界面切换模型 (h-BN 1T1M)
  ├── engine/             仿真与拟合引擎
  │   ├── simulator.py    仿真主循环 (filament → transport → thermal)
  │   └── fitter.py       参数拟合 (DE + L-BFGS-B)
  ├── ui/                 界面层
  │   ├── sidebar.py      侧边栏参数控件
  │   ├── plots.py        Plotly 图表
  │   ├── results.py      指标卡片
  │   └── translations.py 中英文翻译 (75+38 键)
  ├── utils/              工具函数
  │   ├── constants.py    物理常数
  │   └── helpers.py      辅助函数 (电压扫描、工程计数法)
  └── data/               数据层
      └── experiment_loader.py  实验数据加载 (Nature h-BN)
"""

from __future__ import annotations
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from engine.simulator import Simulator
from engine.fitter import fit_interface_model
from models.interface_switching import InterfaceSwitchingModel
from data.experiment_loader import load_nature_dataset, ExperimentData
from ui.sidebar import build_sidebar
from ui.plots import (
    plot_iv_curves, plot_filament_evolution, plot_temperature,
    plot_variability_histogram, plot_experiment_overview,
    plot_fit_comparison, plot_variability_heatmap,
)
from ui.results import render_metric_cards
from ui.translations import t, init_language

st.set_page_config(
    page_title="VULCAN-2D",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_language()

# ── Custom CSS ──
st.markdown("""
<style>
    .stMetric { border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px; }
    .stMetric:hover { border-color: #1f77b4; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Top-level tab: Simulation | Experiment ──
tab_sim, tab_exp = st.tabs(["Simulation", "Experiment Data"])

# ===================================================================
# TAB 1: Simulation (original)
# ===================================================================
with tab_sim:
    params = build_sidebar()

    st.title(t("app_title"))
    st.caption(t("app_subtitle"))

    if not params.get("_run", False):
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.markdown(t("welcome_desc"))
            st.markdown(t("welcome_device_structure"))
            mat = params.get("material", "h-BN")
            thick = params.get("thickness", 5e-9) * 1e9
            elec = params.get("electrode", "Au")
            st.markdown(f"""
            ```
                ┌──────────────┐
                │  {elec:>10s}  │  {t('welcome_top_electrode')}
                ├──────────────┤
                │  {mat:>10s}  │  {t('welcome_switching_layer')}
                │              │     ({thick:.1f} nm)
                ├──────────────┤
                │  {elec:>10s}  │  {t('welcome_bottom_electrode')}
                └──────────────┘
            ```
            """)
        with col_b:
            st.info(t("welcome_hint"))
    else:
        with st.spinner(t("running")):
            sim = Simulator(params)
            results = sim.run()

        render_metric_cards(results)
        st.divider()
        st.plotly_chart(plot_iv_curves(results), use_container_width=True)

        tab_t, tab_f, tab_v = st.tabs([
            t("tab_temperature"), t("tab_filament"), t("tab_variability"),
        ])
        with tab_t:
            st.plotly_chart(plot_temperature(results), use_container_width=True)
        with tab_f:
            st.plotly_chart(plot_filament_evolution(results), use_container_width=True)
        with tab_v:
            if len(results["cycles"]) > 1:
                st.plotly_chart(plot_variability_histogram(results), use_container_width=True)
            else:
                st.info(t("variability_hint"))

        with st.expander(t("raw_data")):
            cycle_idx = st.selectbox(t("raw_data_cycle"), range(len(results["cycles"])), index=0)
            cycle = results["cycles"][cycle_idx]
            st.write(f"**{t('raw_data_cycle')} {cycle_idx + 1}** — {len(cycle['v'])} {t('raw_data_points')}")
            c1, c2 = st.columns(2)
            with c1:
                st.metric(t("raw_data_v_range"), f"{cycle['v'].min():.2f} → {cycle['v'].max():.2f} V")
                st.metric(t("raw_data_i_range"), f"{cycle['i'].min()*1e3:.4f} → {cycle['i'].max()*1e3:.4f} mA")
            with c2:
                st.metric(t("raw_data_t_max"), f"{cycle['T'].max():.1f} K")
                st.metric(t("raw_data_r_range"), f"{cycle['r'].min()*1e9:.3f} → {cycle['r'].max()*1e9:.3f} nm")

# ===================================================================
# TAB 2: Experiment Data
# ===================================================================
with tab_exp:
    st.title(t("exp_tab_title"))
    st.caption(t("exp_tab_caption"))

    # ── Load data ──
    DATA_PATH = "/Users/fanxiang/experiment data/nature h-BN"

    try:
        exp_data = load_nature_dataset(DATA_PATH)
        set_cycles = exp_data["set"]
        reset_cycles = exp_data["reset"]
        n_set = len(set_cycles)
        n_reset = len(reset_cycles)

        # ── Summary metrics row ──
        s1 = set_cycles[0]
        r1 = reset_cycles[0] if reset_cycles else None
        cols = st.columns(6)
        with cols[0]:
            st.metric(t("exp_metric_set_cycles"), str(n_set))
        with cols[1]:
            st.metric(t("exp_metric_erase_cycles"), str(n_reset))
        with cols[2]:
            st.metric(t("exp_metric_v_sweep"), f"{s1.v_range[0]:.1f} → {s1.v_range[1]:.1f} V")
        with cols[3]:
            st.metric(t("exp_metric_i_range"), f"{s1.current.min()*1e9:.1f} nA → {s1.i_max*1e6:.1f} µA")
        with cols[4]:
            on_off = s1.i_max / abs(s1.current[:10]).mean() if abs(s1.current[:10]).mean() > 0 else 0
            st.metric(t("exp_metric_on_off"), f"{on_off:,.0f}×")
        with cols[5]:
            st.metric(t("exp_metric_points"), str(len(s1.voltage)))

        st.divider()

        # ── Overview plot ──
        st.plotly_chart(plot_experiment_overview(exp_data, log_y=True), use_container_width=True)

        # ── Tabs ──
        exp_tab1, exp_tab2, exp_tab3 = st.tabs([
            t("exp_tab_fitting"), t("exp_tab_heatmap"), t("exp_tab_erase"),
        ])

        with exp_tab1:
            st.subheader(t("exp_fitting_title"))

            col_l, col_r = st.columns([1, 2])
            with col_l:
                with st.expander(t("exp_model_eq_title"), expanded=True):
                    st.markdown(t("exp_state_var"))
                    st.latex(r"""
                    \frac{ds}{dt} = k_{\text{set}} \cdot
                    \sigma(V-V_{\text{set,th}}) \cdot (1-s)
                    - k_{\text{reset}} \cdot
                    \sigma(V_{\text{reset,th}}-V) \cdot s
                    """)
                    st.caption(t("exp_sigma_caption"))

                    st.markdown(t("exp_barrier_label"))
                    st.latex(r"""
                    \phi_B(s) = \phi_{B0} - s \cdot (\phi_{B0} - \phi_{B,\min})
                    """)

                    st.markdown(t("exp_current_label"))
                    st.latex(r"""
                    I_{\text{mem}}(V>0) = I_0 \cdot
                    e^{-\phi_B(s)/k_BT} \cdot
                    \left(e^{qV / n k_B T} - 1\right)
                    """)

                    st.markdown(t("exp_compliance_label"))
                    st.latex(r"""
                    I_{\text{final}} = I_{\text{sat}} \cdot
                    \tanh\!\left(\frac{|I_{\text{mem}}|}{I_{\text{sat}}}\right)
                    \cdot \text{sgn}(I_{\text{mem}})
                    """)

                    st.markdown(t("exp_loss_label"))
                    st.latex(r"""
                    \mathcal{L} = \frac{1}{N}\sum_{i=1}^{N}
                    \left(\log_{10}|I_{\text{sim}}(V_i)|
                    - \log_{10}|I_{\text{exp}}(V_i)|\right)^2
                    """)

                    st.caption(t("exp_params_label"))

                st.markdown(t("exp_fitting_hint"))

                fit_btn = st.button(t("exp_run_fit_btn"), type="primary", use_container_width=True)

                if "fit_result" in st.session_state:
                    fr = st.session_state["fit_result"]
                    st.markdown(t("exp_fitted_params"))
                    bp = fr["best_params"]
                    for k, v in bp.items():
                        st.caption(f"`{k}` = {v:.4g}")
                    st.caption(f"{t('exp_fit_mse')} = {fr['mse']:.6f}")
                    st.caption(f"{t('exp_fit_time')} = {fr['elapsed_s']:.2f}s")

            with col_r:
                if fit_btn:
                    with st.spinner(t("exp_fit_running")):
                        mean_data = exp_data["set_mean"]
                        result = fit_interface_model(mean_data)
                        st.session_state["fit_result"] = result

                if "fit_result" in st.session_state:
                    fr = st.session_state["fit_result"]
                    st.plotly_chart(
                        plot_fit_comparison(exp_data, fr["i_fitted"], fr, log_y=True),
                        use_container_width=True,
                    )
                else:
                    st.info(t("exp_fit_waiting"))

        with exp_tab2:
            st.plotly_chart(plot_variability_heatmap(exp_data), use_container_width=True)
            st.markdown(t("exp_heatmap_analysis"))

        with exp_tab3:
            st.subheader(t("exp_erase_title"))
            if reset_cycles:
                fig = go.Figure()
                for c in reset_cycles[:10]:
                    fig.add_trace(go.Scatter(
                        x=c.voltage, y=c.current_ua,
                        mode="lines", line=dict(width=0.8),
                        opacity=0.4, showlegend=False,
                        hovertemplate="V=%{x:.2f}V I=%{y:.3f}µA<extra></extra>",
                    ))
                fig.update_layout(
                    title=t("exp_erase_plot_title"),
                    xaxis_title=t("plot_voltage"),
                    yaxis_title=t("exp_current_ua"),
                    template="plotly_white",
                    height=400,
                    margin=dict(l=40, r=20, t=40, b=40),
                )
                st.plotly_chart(fig, use_container_width=True)

    except FileNotFoundError as e:
        st.error(f"{t('exp_data_not_found')}{DATA_PATH}")
        st.info(t("exp_data_hint"))
