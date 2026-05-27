"""Sidebar parameter controls for VULCAN-2D."""

from __future__ import annotations
import streamlit as st
from utils.constants import Q_E
from ui.translations import t, toggle_language


def build_sidebar() -> dict:
    """Render sidebar controls and return parameter dict."""
    st.sidebar.title(t("app_title"))
    st.sidebar.caption(t("sidebar_subtitle"))

    params: dict = {}

    # ── Language ──
    with st.sidebar.expander(t("lang_setting_group"), expanded=False):
        cur_lang = st.session_state.get("lang", "zh")
        lang_display = f"{'中文' if cur_lang == 'zh' else 'English'} → {'English' if cur_lang == 'zh' else '中文'}"
        st.button(
            f"{t('lang_label')}: {lang_display}",
            on_click=toggle_language,
            use_container_width=True,
        )

    # ── Device Structure ──
    with st.sidebar.expander(t("section_device"), expanded=True):
        params["material"] = st.selectbox(
            t("label_material"),
            ["h-BN", "Graphene oxide", "MoS₂", "WS₂", t("material_custom")],
            index=0,
        )
        params["thickness"] = st.slider(
            t("label_thickness"), 1.0, 20.0, 5.0, 0.5
        ) * 1e-9
        params["eps_r"] = st.slider(
            t("label_eps_r"), 1.0, 20.0, 4.0, 0.5
        )
        params["electrode"] = st.selectbox(
            t("label_electrode"), ["Au", "Ag", "Ti/Au", "Cu", "Pt"], index=0
        )

    # ── Filament Parameters ──
    with st.sidebar.expander(t("section_filament"), expanded=False):
        params["r_min"] = st.slider(
            t("label_r_min"), 0.01, 0.5, 0.05, 0.01
        ) * 1e-9
        params["r_max"] = st.slider(
            t("label_r_max"), 0.5, 5.0, 2.0, 0.1
        ) * 1e-9
        params["migration_barrier"] = st.slider(
            t("label_migration_barrier"), 0.1, 1.5, 0.6, 0.05
        ) * Q_E
        params["growth_rate_coeff"] = st.slider(
            t("label_growth_rate"), 0.01, 10.0, 1.0, 0.1
        ) * 1e-4
        params["dissolution_coeff"] = st.slider(
            t("label_dissolution_rate"), 0.01, 10.0, 5.0, 0.1
        ) * 1e-4
        params["qpc_channels"] = st.slider(
            t("label_qpc_channels"), 1, 20, 5, 1
        )
        params["transmission"] = st.slider(
            t("label_transmission"), 0.1, 1.0, 0.8, 0.05
        )
        params["trap_depth"] = st.slider(
            t("label_trap_depth"), 0.1, 1.0, 0.4, 0.05
        ) * Q_E

    # ── Electrical Conditions ──
    with st.sidebar.expander(t("section_electrical"), expanded=False):
        params["v_max"] = st.slider(
            t("label_v_max"), 0.5, 5.0, 2.0, 0.1
        )
        params["v_step"] = st.slider(
            t("label_v_step"), 5, 100, 20, 5
        ) * 1e-3
        params["icc"] = st.slider(
            t("label_icc"), 0.0, 10.0, 5.0, 0.1
        ) * 1e-3
        params["n_cycles"] = st.slider(
            t("label_n_cycles"), 1, 30, 1, 1
        )
        params["T_ambient"] = st.slider(
            t("label_T_ambient"), 200, 500, 300, 10
        )

    # ── Variability ──
    with st.sidebar.expander(t("section_variability"), expanded=False):
        params["variability_enabled"] = st.checkbox(t("label_variability_enabled"), value=False)
        params["c2c_sigma"] = st.slider(
            t("label_c2c_sigma"), 0.0, 20.0, 5.0, 0.5
        ) / 100.0
        params["d2d_sigma"] = st.slider(
            t("label_d2d_sigma"), 0.0, 30.0, 10.0, 0.5
        ) / 100.0
        params["seed"] = st.number_input(t("label_seed"), 0, 99999, 42)

    # ── Thermal ──
    with st.sidebar.expander(t("section_thermal"), expanded=False):
        params["thermal_resistance"] = 10.0 ** st.slider(
            t("label_thermal_resistance"), 3.0, 9.0, 4.0, 0.1
        )
        params["heat_capacity"] = 10.0 ** st.slider(
            t("label_heat_capacity"), -18.0, -10.0, -13.0, 0.5
        )

    # ── Run Button ──
    st.sidebar.divider()
    params["_run"] = st.sidebar.button(t("run_button"), type="primary", use_container_width=True)

    return params
