#!/usr/bin/env python3
"""Compare Tupa and the prototype mHEM code against Grcev Fig. 12 data."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


RHO_VALUES = (30.0, 300.0, 3000.0)


def interpolated_magnitude(frame: pd.DataFrame, rho: float, frequencies: np.ndarray) -> np.ndarray:
    case = frame.loc[frame["rho_ohm_m"] == rho].sort_values("frequency_hz")
    return np.interp(np.log10(frequencies), np.log10(case["frequency_hz"]), case["z_magnitude_ohm"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tupa", required=True, type=Path)
    parser.add_argument("--mhem", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--plot", required=True, type=Path)
    args = parser.parse_args()

    tupa = pd.read_csv(args.tupa)
    mhem = pd.read_csv(args.mhem)
    combined = pd.concat([tupa, mhem], ignore_index=True)
    args.results.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(args.results, index=False)

    raw_reference = pd.read_excel(args.reference, sheet_name=0, header=None)
    metrics: list[dict[str, float | str]] = []
    reference_cases: dict[float, tuple[np.ndarray, np.ndarray]] = {}

    for column, rho in zip((0, 2, 4), RHO_VALUES):
        values = raw_reference.iloc[3:, column : column + 2].dropna().astype(float)
        reference_frequency = values.iloc[:, 0].to_numpy()
        reference_magnitude = values.iloc[:, 1].to_numpy()
        reference_cases[rho] = reference_frequency, reference_magnitude

        predicted = {}
        for solver, frame in (("Tupa", tupa), ("mHEM", mhem)):
            predicted[solver] = interpolated_magnitude(frame, rho, reference_frequency)
            relative_error = (predicted[solver] - reference_magnitude) / reference_magnitude
            metrics.append(
                {
                    "comparison": f"{solver} vs full-wave reference",
                    "rho_ohm_m": rho,
                    "points": len(reference_frequency),
                    "mean_abs_percent_error": 100 * np.mean(np.abs(relative_error)),
                    "median_abs_percent_error": 100 * np.median(np.abs(relative_error)),
                    "max_abs_percent_error": 100 * np.max(np.abs(relative_error)),
                    "relative_l2_percent": 100 * np.linalg.norm(predicted[solver] - reference_magnitude) / np.linalg.norm(reference_magnitude),
                }
            )

        solver_difference = (predicted["Tupa"] - predicted["mHEM"]) / predicted["mHEM"]
        metrics.append(
            {
                "comparison": "Tupa vs mHEM at reference frequencies",
                "rho_ohm_m": rho,
                "points": len(reference_frequency),
                "mean_abs_percent_error": 100 * np.mean(np.abs(solver_difference)),
                "median_abs_percent_error": 100 * np.median(np.abs(solver_difference)),
                "max_abs_percent_error": 100 * np.max(np.abs(solver_difference)),
                "relative_l2_percent": 100 * np.linalg.norm(predicted["Tupa"] - predicted["mHEM"]) / np.linalg.norm(predicted["mHEM"]),
            }
        )

    metrics_frame = pd.DataFrame(metrics)
    metrics_frame.to_csv(args.metrics, index=False)

    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharex="col")
    colors = {"Tupa": "#0072B2", "mHEM": "#D55E00"}
    for index, rho in enumerate(RHO_VALUES):
        reference_frequency, reference_magnitude = reference_cases[rho]
        magnitude_axis = axes[0, index]
        error_axis = axes[1, index]
        magnitude_axis.scatter(reference_frequency, reference_magnitude, s=24,
                               facecolors="none", edgecolors="black",
                               label="Full-wave reference", zorder=3)
        for solver, frame in (("Tupa", tupa), ("mHEM", mhem)):
            case = frame.loc[frame["rho_ohm_m"] == rho].sort_values("frequency_hz")
            magnitude_axis.plot(case["frequency_hz"], case["z_magnitude_ohm"],
                                color=colors[solver], linewidth=1.8, label=solver)
            prediction = interpolated_magnitude(frame, rho, reference_frequency)
            error = 100 * (prediction - reference_magnitude) / reference_magnitude
            error_axis.plot(reference_frequency, error, marker="o", markersize=3,
                            color=colors[solver], linewidth=1.2, label=solver)
        magnitude_axis.set_xscale("log")
        magnitude_axis.set_yscale("log")
        magnitude_axis.grid(True, which="both", alpha=0.25)
        magnitude_axis.set_title(f"ρ = {rho:g} Ω·m")
        error_axis.axhline(0, color="black", linewidth=0.8)
        error_axis.set_xscale("log")
        error_axis.grid(True, which="both", alpha=0.25)
        error_axis.set_xlabel("Frequency (Hz)")
        if index == 0:
            magnitude_axis.set_ylabel("|Zₕ| (Ω)")
            error_axis.set_ylabel("Error vs reference (%)")
            magnitude_axis.legend(loc="best")
            error_axis.legend(loc="best")
    fig.suptitle("10 m horizontal electrode: Tupa and mHEM vs Grcev full-wave reference")
    fig.tight_layout()
    args.plot.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.plot, dpi=180, bbox_inches="tight")


if __name__ == "__main__":
    main()
