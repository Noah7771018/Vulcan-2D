"""Plotly-based visualization functions for VULCAN-2D."""

from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from ui.translations import t


def plot_iv_curves(results: dict) -> go.Figure:
    """Plot I-V curves for all cycles, with variability overlay."""
    cycles = results["cycles"]
    fig = go.Figure()

    for idx, cycle in enumerate(cycles):
        if len(cycles) > 1:
            name = f"{t('plot_iv_cycle')} {idx + 1}"
        else:
            name = t("plot_iv_curve")
        opacity = 0.8 if len(cycles) == 1 else 0.5
        color = "steelblue" if idx == 0 else "lightsteelblue"
        fig.add_trace(go.Scatter(
            x=cycle["v"],
            y=cycle["i"] * 1e3,
            mode="lines",
            name=name,
            line=dict(color=color, width=1.5),
            opacity=opacity,
            hovertemplate=f"V = %{{x:.3f}} V<br>I = %{{y:.4f}} mA<extra></extra>",
        ))

    fig.add_hline(y=0, line_color="gray", line_width=0.5)
    fig.add_vline(x=0, line_color="gray", line_width=0.5)

    fig.update_layout(
        title=t("plot_iv_title"),
        xaxis_title=t("plot_voltage"),
        yaxis_title=t("plot_current"),
        template="plotly_white",
        hovermode="x unified",
        height=420,
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25),
    )
    return fig


def plot_filament_evolution(results: dict) -> go.Figure:
    """Plot filament radius vs voltage."""
    cycles = results["cycles"]
    fig = go.Figure()

    for idx, cycle in enumerate(cycles):
        color = "coral" if idx == 0 else "peachpuff"
        if len(cycles) > 1:
            name = f"{t('plot_filament_label')} {idx + 1}"
        else:
            name = t("plot_filament_label")
        fig.add_trace(go.Scatter(
            x=cycle["v"],
            y=cycle["r"] * 1e9,
            mode="lines",
            name=name,
            line=dict(color=color, width=1.8),
            opacity=0.8 if idx == 0 else 0.4,
            hovertemplate=f"V = %{{x:.3f}} V<br>r = %{{y:.3f}} nm<extra></extra>",
        ))

    fig.update_layout(
        title=t("plot_filament_title"),
        xaxis_title=t("plot_voltage"),
        yaxis_title=t("plot_filament_radius"),
        template="plotly_white",
        height=380,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig


def plot_temperature(results: dict) -> go.Figure:
    """Plot filament temperature vs voltage."""
    cycles = results["cycles"]
    fig = go.Figure()

    for idx, cycle in enumerate(cycles):
        color = "crimson" if idx == 0 else "lightcoral"
        if len(cycles) > 1:
            name = f"{t('plot_temp_series')} {idx + 1}"
        else:
            name = t("plot_temp_series")
        fig.add_trace(go.Scatter(
            x=cycle["v"],
            y=cycle["T"],
            mode="lines",
            name=name,
            line=dict(color=color, width=1.8),
            opacity=0.8 if idx == 0 else 0.4,
            hovertemplate=f"V = %{{x:.3f}} V<br>T = %{{y:.1f}} K<extra></extra>",
        ))

    fig.update_layout(
        title=t("plot_temperature_title"),
        xaxis_title=t("plot_voltage"),
        yaxis_title=t("plot_temperature_label"),
        template="plotly_white",
        height=380,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig


def plot_variability_histogram(results: dict) -> go.Figure:
    """Plot distribution of key metrics across cycles."""
    metrics = results["metrics"]
    if len(metrics) < 2:
        return go.Figure().update_layout(
            title=t("plot_variability_hint"),
            template="plotly_white",
            height=380,
        )

    v_sets = [m.get("v_set", np.nan) for m in metrics]
    v_resets = [m.get("v_reset", np.nan) for m in metrics]
    valid_set = [v for v in v_sets if not np.isnan(v)]
    valid_reset = [v for v in v_resets if not np.isnan(v)]

    fig = go.Figure()
    if valid_set:
        fig.add_trace(go.Histogram(
            x=valid_set, name="V<sub>set</sub>",
            marker_color="steelblue", opacity=0.7, nbinsx=max(5, len(valid_set) // 2),
        ))
    if valid_reset:
        fig.add_trace(go.Histogram(
            x=valid_reset, name="V<sub>reset</sub>",
            marker_color="coral", opacity=0.7, nbinsx=max(5, len(valid_reset) // 2),
        ))

    fig.update_layout(
        title=t("plot_variability_title"),
        xaxis_title=t("plot_voltage"),
        yaxis_title=t("plot_variability_count"),
        template="plotly_white",
        height=380,
        margin=dict(l=40, r=20, t=40, b=40),
        barmode="overlay",
    )
    return fig
