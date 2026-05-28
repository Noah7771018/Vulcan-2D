"""Plotly 可视化函数。

分类:
  - Simulation Tab 用图: I-V 曲线、细丝演化、温度、变异性分布
  - Experiment Tab 用图: 实验总览、拟合对比、变异性热力图
"""

from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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


def plot_experiment_overview(exp_data: dict, log_y: bool = True) -> go.Figure:
    """Overview: all experimental set cycles overlaid with mean ± std.

    Args:
        log_y: Use log10 Y-axis (recommended: HRS nA and LRS µA both visible).
    """
    cycles = exp_data.get("set", [])
    if not cycles:
        return _empty_fig("No experimental data loaded")

    fig = go.Figure()

    # Use abs(current) for log scale (current is positive in rising sweep)
    for c in cycles:
        fig.add_trace(go.Scatter(
            x=c.voltage, y=abs(c.current) if log_y else c.current_ua,
            mode="lines", line=dict(color="lightsteelblue", width=0.5),
            opacity=0.3, showlegend=False,
            hovertemplate="V=%{x:.2f}V I=%{y:.3e}A<extra></extra>" if log_y else "V=%{x:.2f}V I=%{y:.2f}µA<extra></extra>",
        ))

    mean_data = exp_data.get("set_mean")
    if mean_data is not None:
        fig.add_trace(go.Scatter(
            x=mean_data.voltage,
            y=abs(mean_data.current) if log_y else mean_data.current_ua,
            mode="lines", name="Mean", line=dict(color="steelblue", width=2.5),
        ))

    # ±1σ band (skip on log scale — would look messy)
    if not log_y:
        std_data = exp_data.get("set_std")
        if mean_data is not None and std_data is not None:
            upper = (mean_data.current + std_data.current) * 1e6
            lower = np.maximum(mean_data.current - std_data.current, 0) * 1e6
            fig.add_trace(go.Scatter(
                x=np.concatenate([mean_data.voltage, mean_data.voltage[::-1]]),
                y=np.concatenate([upper, lower[::-1]]),
                fill="toself", fillcolor="rgba(70,130,180,0.15)",
                line=dict(width=0), name="±1σ", showlegend=True,
            ))

    fig.update_layout(
        title=t("exp_overview_title"),
        xaxis_title=t("plot_voltage"),
        yaxis_title="Current [A]" if log_y else t("exp_current_ua"),
        yaxis_type="log" if log_y else "linear",
        template="plotly_white",
        height=420,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig


def plot_fit_comparison(exp_data, i_fitted: np.ndarray, fit_result: dict,
                        log_y: bool = True) -> go.Figure:
    """Comparison: experimental mean vs fitted model curve.

    Args:
        log_y: Use log10 Y-axis (recommended for 5+ decades of current).
    """
    mean_data = exp_data.get("set_mean")
    if mean_data is None:
        return _empty_fig("No mean data available")

    fig = go.Figure()

    y_exp = abs(mean_data.current) if log_y else mean_data.current_ua
    y_fit = abs(i_fitted) if log_y else i_fitted * 1e6

    # Experimental mean
    fig.add_trace(go.Scatter(
        x=mean_data.voltage, y=y_exp,
        mode="lines", name=t("exp_mean_label"),
        line=dict(color="steelblue", width=2),
    ))

    # Fitted model
    fig.add_trace(go.Scatter(
        x=mean_data.voltage, y=y_fit,
        mode="lines", name=t("exp_model_label"),
        line=dict(color="crimson", width=2, dash="dash"),
    ))

    # ±1σ band (skip on log scale)
    if not log_y:
        std_data = exp_data.get("set_std")
        if std_data is not None:
            upper = (mean_data.current + std_data.current) * 1e6
            lower = np.maximum(mean_data.current - std_data.current, 0) * 1e6
            fig.add_trace(go.Scatter(
                x=np.concatenate([mean_data.voltage, mean_data.voltage[::-1]]),
                y=np.concatenate([upper, lower[::-1]]),
                fill="toself", fillcolor="rgba(70,130,180,0.1)",
                line=dict(width=0), name="±1σ",
            ))

    mse = fit_result.get("mse", 0)
    fig.update_layout(
        title=f"{t('exp_fit_compare_title')} (MSE={mse:.4f})",
        xaxis_title=t("plot_voltage"),
        yaxis_title="Current [A]" if log_y else t("exp_current_ua"),
        yaxis_type="log" if log_y else "linear",
        template="plotly_white",
        height=420,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig


def plot_variability_heatmap(exp_data: dict) -> go.Figure:
    """Heatmap showing cycle-to-cycle variability of all set cycles."""
    cycles = exp_data.get("set", [])
    if not cycles:
        return _empty_fig("No data")

    n_cycles = len(cycles)
    v_ref = cycles[0].voltage

    # Build matrix: rows = cycles, cols = voltage points
    i_matrix = np.zeros((n_cycles, len(v_ref)))
    for idx, c in enumerate(cycles):
        i_matrix[idx, :] = np.log10(np.abs(c.current) + 1e-12)

    fig = go.Figure(data=go.Heatmap(
        z=i_matrix,
        x=v_ref,
        y=list(range(1, n_cycles + 1)),
        colorscale="Viridis",
        colorbar=dict(title="log10(|I|) [A]"),
        hovertemplate="V=%{x:.2f}V Cycle=%{y} logI=%{z:.2f}<extra></extra>",
    ))

    fig.update_layout(
        title=t("exp_heatmap_title"),
        xaxis_title=t("plot_voltage"),
        yaxis_title="Cycle #",
        template="plotly_white",
        height=400,
        margin=dict(l=40, r=20, t=40, b=40),
    )
    return fig


def _empty_fig(msg: str) -> go.Figure:
    """Return an empty figure with a message."""
    fig = go.Figure()
    fig.update_layout(
        title=msg,
        template="plotly_white",
        height=380,
    )
    return fig

