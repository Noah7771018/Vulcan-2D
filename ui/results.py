"""Results display panel for VULCAN-2D."""

from __future__ import annotations
import streamlit as st
import numpy as np
from utils.helpers import format_engineering
from ui.translations import t


def render_metric_cards(results: dict) -> None:
    """Display key metrics in a row of cards."""
    metrics = results.get("metrics", [])
    if not metrics:
        return

    m = metrics[0]

    cols = st.columns(5)

    with cols[0]:
        v_set = m.get("v_set", np.nan)
        delta = None
        if len(metrics) > 1 and not np.isnan(v_set):
            sigma_vs = np.nanstd([mm.get("v_set", np.nan) for mm in metrics])
            if not np.isnan(sigma_vs):
                delta = f"σ={sigma_vs:.3f} V"
        st.metric(
            t("metric_v_set"),
            f"{v_set:.3f} V" if not np.isnan(v_set) else "N/A",
            delta=delta,
            delta_color="off",
        )

    with cols[1]:
        v_reset = m.get("v_reset", np.nan)
        st.metric(
            t("metric_v_reset"),
            f"{v_reset:.3f} V" if not np.isnan(v_reset) else "N/A",
        )

    with cols[2]:
        R_lrs = m.get("R_lrs", np.nan)
        st.metric(
            t("metric_R_lrs"),
            format_engineering(R_lrs, "Ω") if not np.isnan(R_lrs) else "N/A",
        )

    with cols[3]:
        R_hrs = m.get("R_hrs", np.nan)
        st.metric(
            t("metric_R_hrs"),
            format_engineering(R_hrs, "Ω") if not np.isnan(R_hrs) else "N/A",
        )

    with cols[4]:
        ratio = m.get("on_off_ratio", np.nan)
        st.metric(
            t("metric_on_off"),
            f"{ratio:.1f}×" if not np.isnan(ratio) else "N/A",
        )

    cols2 = st.columns(2)
    with cols2[0]:
        T_max = m.get("T_max", np.nan)
        st.metric(
            t("metric_T_max"),
            f"{T_max:.1f} K" if not np.isnan(T_max) else "N/A",
        )
    with cols2[1]:
        elapsed = results.get("elapsed_s", 0)
        st.metric(t("metric_elapsed"), f"{elapsed:.3f} s")
