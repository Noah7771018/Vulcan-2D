"""VULCAN-2D — Streamlit app entry point.

面向二维材料忆阻器的多尺度物理建模与仿真器
Variability-aware Unified simulator for Layered-material Conduction ANalysis
"""

from __future__ import annotations
import streamlit as st
from engine.simulator import Simulator
from ui.sidebar import build_sidebar
from ui.plots import plot_iv_curves, plot_filament_evolution, plot_temperature, plot_variability_histogram
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

# ── Sidebar ──
params = build_sidebar()

# ── Main Panel ──
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

    tab1, tab2, tab3 = st.tabs([
        t("tab_temperature"),
        t("tab_filament"),
        t("tab_variability"),
    ])

    with tab1:
        st.plotly_chart(plot_temperature(results), use_container_width=True)

    with tab2:
        st.plotly_chart(plot_filament_evolution(results), use_container_width=True)

    with tab3:
        if len(results["cycles"]) > 1:
            st.plotly_chart(plot_variability_histogram(results), use_container_width=True)
        else:
            st.info(t("variability_hint"))

    with st.expander(t("raw_data")):
        cycle_idx = st.selectbox(
            t("raw_data_cycle"),
            range(len(results["cycles"])),
            index=0,
        )
        cycle = results["cycles"][cycle_idx]
        st.write(f"**{t('raw_data_cycle')} {cycle_idx + 1}** — {len(cycle['v'])} {t('raw_data_points')}")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(t("raw_data_v_range"), f"{cycle['v'].min():.2f} → {cycle['v'].max():.2f} V")
            st.metric(t("raw_data_i_range"), f"{cycle['i'].min()*1e3:.4f} → {cycle['i'].max()*1e3:.4f} mA")
        with col2:
            st.metric(t("raw_data_t_max"), f"{cycle['T'].max():.1f} K")
            st.metric(t("raw_data_r_range"), f"{cycle['r'].min()*1e9:.3f} → {cycle['r'].max()*1e9:.3f} nm")
