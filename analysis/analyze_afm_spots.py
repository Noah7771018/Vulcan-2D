#!/usr/bin/env python3
"""Analyze the projected-area distribution of sputtered h-BN CAFM spots."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "vulcan2d-matplotlib")
)
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = (
    ROOT.parent
    / "AFM"
    / "Conductive spot size distributions defect for sputter hBN.txt"
)
DEFAULT_CSV = ROOT / "analysis" / "afm_spot_distribution.csv"
DEFAULT_JSON = ROOT / "analysis" / "afm_spot_summary.json"
DEFAULT_FIGURE = ROOT / "analysis" / "figures" / "11_afm_conductive_spot_distribution.png"


def parse_distribution(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return projected-area bin centers [m2] and integer object counts."""
    pattern = re.compile(r"^\s*([0-9.eE+-]+)\s+(\d+)\s*$")
    rows: list[tuple[float, int]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            rows.append((float(match.group(1)), int(match.group(2))))
    if not rows:
        raise ValueError(f"No numeric area/count rows found in {path}")
    data = np.asarray(rows, dtype=float)
    return data[:, 0], data[:, 1].astype(int)


def weighted_quantile(values: np.ndarray, counts: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    sorted_values = values[order]
    cumulative = np.cumsum(counts[order])
    index = int(np.searchsorted(cumulative, q * cumulative[-1], side="left"))
    return float(sorted_values[min(index, len(sorted_values) - 1)])


def summarize(
    area_m2: np.ndarray,
    counts: np.ndarray,
    scan_width_um: float,
    scan_height_um: float,
) -> dict[str, object]:
    diameter_nm = 2.0 * np.sqrt(area_m2 / np.pi) * 1e9
    total_count = int(np.sum(counts))
    total_projected_area_um2 = float(np.sum(area_m2 * counts) * 1e12)
    scan_area_um2 = scan_width_um * scan_height_um
    mean_area_m2 = float(np.sum(area_m2 * counts) / total_count)
    mean_diameter_nm = float(np.sum(diameter_nm * counts) / total_count)
    second_area_moment = float(np.sum(area_m2**2 * counts))
    effective_spot_count = (total_projected_area_um2 * 1e-12) ** 2 / second_area_moment
    mode_index = int(np.argmax(counts))
    percentiles = (10, 25, 50, 75, 90, 95, 99)

    return {
        "source_file": str(DEFAULT_INPUT),
        "data_semantics": {
            "column_1": "projected conductive-spot area in square metres",
            "column_2": "number of segmented spots in that area bin",
            "equivalent_diameter_formula": "d_eq = 2*sqrt(A/pi)",
        },
        "scan_assumption": {
            "width_um": scan_width_um,
            "height_um": scan_height_um,
            "basis": "nominal size inferred from the 1 um scale bar in slide 2",
        },
        "spot_count": total_count,
        "nonzero_bins": int(np.count_nonzero(counts)),
        "total_projected_area_um2": total_projected_area_um2,
        "apparent_spot_density_per_um2": total_count / scan_area_um2,
        "apparent_projected_area_fraction": total_projected_area_um2 / scan_area_um2,
        "area_nm2": {
            "mean": mean_area_m2 * 1e18,
            "mode": float(area_m2[mode_index] * 1e18),
            "percentiles": {
                str(p): weighted_quantile(area_m2, counts, p / 100.0) * 1e18
                for p in percentiles
            },
        },
        "equivalent_diameter_nm": {
            "mean": mean_diameter_nm,
            "mode": float(diameter_nm[mode_index]),
            "percentiles": {
                str(p): weighted_quantile(diameter_nm, counts, p / 100.0)
                for p in percentiles
            },
        },
        "count_fraction_below_diameter": {
            "50_nm": float(np.sum(counts[diameter_nm <= 50.0]) / total_count),
            "75_nm": float(np.sum(counts[diameter_nm <= 75.0]) / total_count),
            "100_nm": float(np.sum(counts[diameter_nm <= 100.0]) / total_count),
        },
        "area_heterogeneity": {
            "coefficient_of_variation": float(
                np.sqrt(np.sum(counts * (area_m2 - mean_area_m2) ** 2) / total_count)
                / mean_area_m2
            ),
            "effective_spot_count": float(effective_spot_count),
        },
    }


def write_bin_table(
    path: Path, area_m2: np.ndarray, counts: np.ndarray
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total_count = int(np.sum(counts))
    total_area_m2 = float(np.sum(area_m2 * counts))
    diameter_nm = 2.0 * np.sqrt(area_m2 / np.pi) * 1e9
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "projected_area_m2",
                "equivalent_diameter_nm",
                "count",
                "count_fraction",
                "projected_area_contribution_um2",
                "projected_area_fraction",
            ]
        )
        for area, diameter, count in zip(area_m2, diameter_nm, counts):
            writer.writerow(
                [
                    f"{area:.8e}",
                    f"{diameter:.6f}",
                    int(count),
                    f"{count / total_count:.9f}",
                    f"{area * count * 1e12:.9f}",
                    f"{area * count / total_area_m2:.9f}",
                ]
            )


def make_figure(
    path: Path,
    area_m2: np.ndarray,
    counts: np.ndarray,
    summary: dict[str, object],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    diameter_nm = 2.0 * np.sqrt(area_m2 / np.pi) * 1e9
    total_count = int(np.sum(counts))
    cumulative_count = np.cumsum(counts) / total_count
    cumulative_area = np.cumsum(area_m2 * counts) / np.sum(area_m2 * counts)
    positive = counts > 0

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), constrained_layout=True)

    axes[0].stem(
        diameter_nm[positive],
        counts[positive],
        linefmt="#147d74",
        markerfmt="o",
        basefmt=" ",
    )
    axes[0].set_yscale("log")
    axes[0].set_xlabel("Equivalent circular diameter (nm)")
    axes[0].set_ylabel("Segmented spot count")
    axes[0].set_title("Conductive-spot size distribution")
    median_diameter = float(summary["equivalent_diameter_nm"]["percentiles"]["50"])
    axes[0].axvline(
        median_diameter, color="#d95f02", linestyle="--", linewidth=1.4
    )
    axes[0].text(
        median_diameter + 3,
        1250,
        f"median = {median_diameter:.1f} nm",
        color="#9b3f00",
        fontsize=9,
    )

    axes[1].plot(
        diameter_nm,
        cumulative_count * 100,
        color="#1f6fba",
        linewidth=2.2,
        label="Cumulative spot count",
    )
    axes[1].plot(
        diameter_nm,
        cumulative_area * 100,
        color="#d95f02",
        linewidth=2.2,
        label="Cumulative projected area",
    )
    axes[1].set_xlabel("Equivalent circular diameter (nm)")
    axes[1].set_ylabel("Cumulative fraction (%)")
    axes[1].set_ylim(0, 102)
    axes[1].set_title("Small spots dominate the count")
    axes[1].legend(frameon=False, loc="lower right")

    diameter_summary = summary["equivalent_diameter_nm"]
    count_fraction = summary["count_fraction_below_diameter"]
    note = (
        f"N = {total_count:,}\n"
        f"mean d_eq = {diameter_summary['mean']:.1f} nm\n"
        f"P90 d_eq = {diameter_summary['percentiles']['90']:.1f} nm\n"
        f"d_eq <= 100 nm: {100 * count_fraction['100_nm']:.1f}%"
    )
    axes[1].text(
        0.04,
        0.96,
        note,
        transform=axes[1].transAxes,
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#c7c7c7", "pad": 5},
    )

    fig.suptitle(
        "Sputtered h-BN CAFM: apparent conductive-region statistics",
        fontsize=13,
        fontweight="bold",
    )
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--scan-width-um", type=float, default=5.0)
    parser.add_argument("--scan-height-um", type=float, default=5.0)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE)
    args = parser.parse_args()

    area_m2, counts = parse_distribution(args.input)
    summary = summarize(area_m2, counts, args.scan_width_um, args.scan_height_um)
    summary["source_file"] = str(args.input.resolve())
    write_bin_table(args.csv, area_m2, counts)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    make_figure(args.figure, area_m2, counts, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
