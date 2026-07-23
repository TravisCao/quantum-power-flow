"""Plot generation for the reproduced paper experiments."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

from .models import PowerFlowResult


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_test_i_trace_plot(
    published: pd.DataFrame,
    classical: pd.DataFrame,
    quantum: pd.DataFrame,
    path: str | Path,
) -> None:
    output = Path(path)
    _ensure_parent(output)
    figure, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
    columns = ["V3", "V4", "theta3_rad", "theta4_rad"]
    labels = ["V3 (p.u.)", "V4 (p.u.)", "θ3 (rad)", "θ4 (rad)"]
    for axis, column, label in zip(axes.flat, columns, labels, strict=True):
        axis.plot(published["iteration"], published[column], marker="o", label="Paper (published)")
        axis.plot(
            classical["iteration"], classical[column], marker="x", label="This repo (classical)"
        )
        axis.plot(
            quantum["iteration"], quantum[column], linestyle="--", label="This repo (quantum)"
        )
        axis.set_ylabel(label)
        axis.grid(True, alpha=0.3)
    for axis in axes[-1, :]:
        axis.set_xlabel("Iteration")
    axes[0, 0].legend()
    figure.suptitle("Normal loading: convergence to the paper's solution")
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def save_test_ii_voltage_plot(
    classical: PowerFlowResult,
    quantum: PowerFlowResult,
    path: str | Path,
) -> None:
    output = Path(path)
    _ensure_parent(output)
    figure, axis = plt.subplots(figsize=(8, 5))
    classical_iterations = np.arange(1, len(classical.history) + 1)
    quantum_iterations = np.arange(1, len(quantum.history) + 1)
    for bus, color in ((0, "C0"), (1, "C1")):
        axis.plot(
            classical_iterations,
            [record.voltage_magnitude[bus] for record in classical.history],
            color=color,
        )
        axis.plot(
            quantum_iterations,
            [record.voltage_magnitude[bus] for record in quantum.history],
            linestyle="--",
            color=color,
        )
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Voltage magnitude (p.u.)")
    axis.set_title("Stressed loading: voltage convergence")
    axis.grid(True, alpha=0.3)
    handles = [
        Line2D([0], [0], color="C0", label="Bus 1 voltage"),
        Line2D([0], [0], color="C1", label="Bus 2 voltage"),
    ]
    axis.legend(handles=handles, loc="upper right")
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def save_stochastic_figure(samples: pd.DataFrame, path: str | Path) -> None:
    output = Path(path)
    _ensure_parent(output)
    figure, axes = plt.subplots(2, 2, figsize=(10, 8), layout="constrained")

    probability_weights = np.ones(len(samples), dtype=float) / len(samples)
    axes[0, 0].hist(samples["V3_pu"], bins=35, weights=probability_weights)
    axes[0, 0].set_xlabel("V3 (p.u.)")
    axes[0, 0].set_ylabel("Probability")
    axes[0, 0].set_title("(a) Bus 3 voltage")

    axes[0, 1].scatter(samples["V3_pu"], samples["V4_pu"], s=4, alpha=0.35)
    axes[0, 1].set_xlabel("V3 (p.u.)")
    axes[0, 1].set_ylabel("V4 (p.u.)")
    axes[0, 1].set_title("(b) Voltage correlation")

    axes[1, 0].scatter(
        samples["P4_injection_pu"],
        samples["P3_load_magnitude_pu"],
        s=4,
        alpha=0.35,
    )
    axes[1, 0].set_xlabel("P4 injection (p.u.)")
    axes[1, 0].set_ylabel("P3 load magnitude (p.u.)")
    axes[1, 0].set_title("(c) Injection correlation")

    axes[1, 1].hist(samples["V4_pu"], bins=35, weights=probability_weights)
    axes[1, 1].set_xlabel("V4 (p.u.)")
    axes[1, 1].set_ylabel("Probability")
    axes[1, 1].set_title("(d) Bus 4 voltage")

    for axis in axes.flat:
        axis.grid(True, alpha=0.2)
        axis.xaxis.set_major_locator(MaxNLocator(4))
    figure.savefig(output, dpi=180)
    plt.close(figure)


def save_phase_precision_plot(frame: pd.DataFrame, path: str | Path) -> None:
    output = Path(path)
    _ensure_parent(output)
    figure, axis = plt.subplots(figsize=(7, 4.5))
    axis.semilogy(
        frame["phase_qubits"],
        frame["relative_solution_error"],
        marker="o",
    )
    axis.set_xlabel("Phase-register qubits")
    axis.set_ylabel("Relative linear-solution error")
    axis.set_title("Finite QPE precision ablation (fixed phase scale)")
    axis.set_xticks(frame["phase_qubits"])
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)
