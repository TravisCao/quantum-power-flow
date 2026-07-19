"""Stochastic QPF experiment with correlated bus-3/bus-4 injections."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .linear import PreparedLinearSystem
from .models import FloatArray, PowerFlowCase
from .network import case_ybus


@dataclass(slots=True)
class StochasticQPFResult:
    samples: pd.DataFrame
    converged: np.ndarray
    iterations: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)


def correlated_active_power_samples(
    case: PowerFlowCase,
    *,
    buses: tuple[int, int] = (2, 3),
    n_samples: int = 5000,
    relative_standard_deviation: float = 0.01,
    correlation: float = 0.75,
    seed: int = 210404888,
) -> np.ndarray:
    """Generate Gaussian active-power injections for two internal bus indices.

    The paper supplies the Gaussian correlation (0.75) but not the marginal variances. The default
    one-percent relative standard deviation is reconstructed from the axes of Fig. 4 and is kept as
    an explicit configurable assumption.
    """

    if n_samples < 1:
        raise ValueError("n_samples must be positive.")
    if relative_standard_deviation <= 0:
        raise ValueError("relative_standard_deviation must be positive.")
    if not -1.0 < correlation < 1.0:
        raise ValueError("correlation must lie strictly between -1 and 1.")

    signed_means = case.specified_power_injection[np.asarray(buses)].real
    magnitudes = np.abs(signed_means)
    standard_deviations = magnitudes * relative_standard_deviation
    covariance = np.outer(standard_deviations, standard_deviations)
    covariance[0, 1] *= correlation
    covariance[1, 0] *= correlation
    rng = np.random.default_rng(seed)
    magnitude_samples = rng.multivariate_normal(magnitudes, covariance, size=n_samples)
    return magnitude_samples * np.sign(signed_means)


def _batched_power_injection(
    voltage: FloatArray,
    angle: FloatArray,
    ybus: np.ndarray,
) -> np.ndarray:
    phasor = voltage * np.exp(1j * angle)
    current = phasor @ ybus.T
    return phasor * np.conjugate(current)


def batched_fast_decoupled_qpf(
    case: PowerFlowCase,
    specified_power_samples: np.ndarray,
    *,
    active_system: PreparedLinearSystem,
    reactive_system: PreparedLinearSystem,
    tolerance: float = 1e-5,
    max_iterations: int = 100,
) -> tuple[FloatArray, FloatArray, np.ndarray, np.ndarray, FloatArray]:
    """Vectorized paper-equation FDLF using prepared finite-register HHL maps."""

    specified = np.asarray(specified_power_samples, dtype=complex)
    if specified.ndim != 2 or specified.shape[1] != case.n_buses:
        raise ValueError(
            f"specified_power_samples must have shape (n_samples, {case.n_buses})."
        )

    n_samples = specified.shape[0]
    voltage = np.broadcast_to(case.initial_voltage_magnitude, (n_samples, case.n_buses)).copy()
    angle = np.broadcast_to(case.initial_voltage_angle_rad, (n_samples, case.n_buses)).copy()
    pq = case.pq_buses
    ybus = case_ybus(case)
    converged = np.zeros(n_samples, dtype=bool)
    convergence_iteration = np.full(n_samples, max_iterations, dtype=int)
    final_mismatch = np.full(n_samples, np.inf, dtype=float)

    for iteration in range(max_iterations + 1):
        calculated = _batched_power_injection(voltage, angle, ybus)
        mismatch = specified[:, pq] - calculated[:, pq]
        delta_p = mismatch.real
        delta_q = mismatch.imag
        final_mismatch = np.maximum(
            np.max(np.abs(delta_p), axis=1),
            np.max(np.abs(delta_q), axis=1),
        )
        newly_converged = (~converged) & (final_mismatch < tolerance)
        convergence_iteration[newly_converged] = iteration
        converged |= newly_converged
        if np.all(converged) or iteration == max_iterations:
            break

        active_mask = ~converged
        rhs_p = np.zeros_like(delta_p)
        rhs_q = np.zeros_like(delta_q)
        rhs_p[active_mask] = delta_p[active_mask] / voltage[np.ix_(active_mask, pq)]
        rhs_q[active_mask] = delta_q[active_mask] / voltage[np.ix_(active_mask, pq)]
        scaled_delta_theta = active_system.solve_many(rhs_p)
        delta_voltage = reactive_system.solve_many(rhs_q)
        angle[:, pq] += scaled_delta_theta / voltage[:, pq]
        voltage[:, pq] += delta_voltage
        if np.any(voltage[:, pq] <= 0) or not np.all(np.isfinite(voltage)):
            raise RuntimeError("Batched stochastic QPF produced an invalid voltage state.")

    return voltage, angle, converged, convergence_iteration, final_mismatch


def run_stochastic_qpf(
    case: PowerFlowCase,
    *,
    active_system: PreparedLinearSystem,
    reactive_system: PreparedLinearSystem,
    n_samples: int = 5000,
    relative_standard_deviation: float = 0.01,
    correlation: float = 0.75,
    seed: int = 210404888,
    tolerance: float = 1e-5,
    max_iterations: int = 100,
) -> StochasticQPFResult:
    sampled_buses = (2, 3)
    active_samples = correlated_active_power_samples(
        case,
        buses=sampled_buses,
        n_samples=n_samples,
        relative_standard_deviation=relative_standard_deviation,
        correlation=correlation,
        seed=seed,
    )
    specified = np.broadcast_to(case.specified_power_injection, (n_samples, case.n_buses)).copy()
    specified[:, sampled_buses[0]] = active_samples[:, 0] + 1j * specified[:, sampled_buses[0]].imag
    specified[:, sampled_buses[1]] = active_samples[:, 1] + 1j * specified[:, sampled_buses[1]].imag

    voltage, angle, converged, iterations, mismatch = batched_fast_decoupled_qpf(
        case,
        specified,
        active_system=active_system,
        reactive_system=reactive_system,
        tolerance=tolerance,
        max_iterations=max_iterations,
    )

    frame = pd.DataFrame(
        {
            "sample": np.arange(n_samples, dtype=int),
            "P3_injection_pu": active_samples[:, 0],
            "P4_injection_pu": active_samples[:, 1],
            "P3_load_magnitude_pu": -active_samples[:, 0],
            "V3_pu": voltage[:, 2],
            "V4_pu": voltage[:, 3],
            "theta3_rad": angle[:, 2],
            "theta4_rad": angle[:, 3],
            "iterations": iterations,
            "max_mismatch": mismatch,
            "converged": converged,
        }
    )
    metadata = {
        "n_samples": n_samples,
        "random_seed": seed,
        "active_power_relative_standard_deviation": relative_standard_deviation,
        "requested_injection_correlation": correlation,
        "empirical_injection_correlation": float(
            np.corrcoef(-active_samples[:, 0], active_samples[:, 1])[0, 1]
        ),
        "empirical_signed_injection_correlation": float(
            np.corrcoef(active_samples[:, 0], active_samples[:, 1])[0, 1]
        ),
        "correlation_convention": "paper_Fig4_positive_bus3_load_magnitude_vs_bus4_injection",
        "empirical_voltage_correlation": float(np.corrcoef(voltage[:, 2], voltage[:, 3])[0, 1]),
        "convergence_rate": float(np.mean(converged)),
        "maximum_iterations_observed": int(np.max(iterations)),
        "tolerance": tolerance,
        "variance_status": "reconstructed_assumption_not_reported_in_paper",
    }
    return StochasticQPFResult(
        samples=frame,
        converged=converged,
        iterations=iterations,
        metadata=metadata,
    )
