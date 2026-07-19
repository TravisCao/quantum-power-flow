"""Classical Newton and quantum-assisted fast-decoupled AC power flow."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np

from .linear import LinearSolveResult, LinearSystemFactory, NumpyLinearSystemFactory
from .models import FloatArray, IterationRecord, PowerFlowCase, PowerFlowResult
from .network import (
    calculate_power_injection,
    case_ybus,
    fast_decoupled_matrices,
    power_mismatch,
)

FastDecoupledFormulation = Literal["paper_equations", "standard_sequential"]


def _maximum_mismatch(delta_p: FloatArray, delta_q: FloatArray) -> float:
    return float(max(np.max(np.abs(delta_p)), np.max(np.abs(delta_q))))


def _compact_linear_metadata(result: LinearSolveResult) -> dict[str, Any]:
    source = result.metadata
    compact: dict[str, Any] = {
        "residual_norm": result.residual_norm,
        "backend": source.get("backend", "unknown"),
    }
    for key in (
        "relative_solution_error_vs_direct",
        "solution_state_fidelity_vs_direct",
        "postselection_probability_phase_zero_ancilla_one",
        "ancilla_one_probability",
        "phase_zero_fraction_given_ancilla_one",
        "imaginary_solution_norm_after_phase_fix",
    ):
        if key in source:
            compact[key] = source[key]
    return compact


def solve_fast_decoupled(
    case: PowerFlowCase,
    *,
    linear_system_factory: LinearSystemFactory | None = None,
    tolerance: float = 1e-5,
    max_iterations: int = 100,
    fixed_iterations: int | None = None,
    b_matrix_mode: str = "full_imaginary_ybus",
    formulation: FastDecoupledFormulation = "paper_equations",
) -> PowerFlowResult:
    """Solve the all-PQ case with constant Hermitian fast-decoupled matrices.

    ``paper_equations`` implements the two normalized equations printed in the paper:

    ``B' (V * Δθ) = ΔP / V`` and ``B'' ΔV = ΔQ / V``.

    Both mismatches are evaluated at the beginning of an iteration, matching Algorithm 1. The
    coefficient matrices are prepared once and reused, so a Qiskit HHL factory builds QPE and the
    reciprocal rotation only once.
    """

    if tolerance <= 0:
        raise ValueError("tolerance must be positive.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1.")
    if fixed_iterations is not None and fixed_iterations < 1:
        raise ValueError("fixed_iterations must be at least 1 when provided.")

    factory = linear_system_factory or NumpyLinearSystemFactory()
    ybus = case_ybus(case)
    b_prime, b_double_prime = fast_decoupled_matrices(case, mode=b_matrix_mode)
    active_system = factory.prepare(b_prime, label="B_prime")
    reactive_system = factory.prepare(b_double_prime, label="B_double_prime")

    voltage = case.initial_voltage_magnitude.astype(float, copy=True)
    angle = case.initial_voltage_angle_rad.astype(float, copy=True)
    pq = case.pq_buses
    history: list[IterationRecord] = []
    limit = fixed_iterations if fixed_iterations is not None else max_iterations

    for iteration in range(1, limit + 1):
        delta_p, delta_q, _ = power_mismatch(case, voltage, angle, ybus)
        pre_update_mismatch = _maximum_mismatch(delta_p, delta_q)
        if fixed_iterations is None and pre_update_mismatch < tolerance:
            break

        if np.any(voltage[pq] <= 0):
            raise RuntimeError(
                "Fast-decoupled iteration produced a non-positive voltage magnitude."
            )

        if formulation == "paper_equations":
            active_result = active_system.solve(delta_p / voltage[pq])
            delta_theta = active_result.solution / voltage[pq]
            reactive_result = reactive_system.solve(delta_q / voltage[pq])
            delta_voltage = reactive_result.solution
            angle[pq] += delta_theta
            voltage[pq] += delta_voltage
        elif formulation == "standard_sequential":
            active_result = active_system.solve(delta_p / voltage[pq])
            delta_theta = active_result.solution
            angle[pq] += delta_theta
            _, delta_q_after_angle, _ = power_mismatch(case, voltage, angle, ybus)
            reactive_result = reactive_system.solve(delta_q_after_angle / voltage[pq])
            delta_voltage = reactive_result.solution
            voltage[pq] += delta_voltage
        else:
            raise ValueError("Unknown fast-decoupled formulation.")

        if not np.all(np.isfinite(voltage)) or not np.all(np.isfinite(angle)):
            raise RuntimeError("Fast-decoupled iteration produced a non-finite state.")
        if np.any(voltage[pq] <= 0):
            raise RuntimeError("Fast-decoupled iteration crossed a non-positive voltage magnitude.")

        post_delta_p, post_delta_q, _ = power_mismatch(case, voltage, angle, ybus)
        post_mismatch = _maximum_mismatch(post_delta_p, post_delta_q)
        history.append(
            IterationRecord(
                iteration=iteration,
                voltage_magnitude=voltage.copy(),
                voltage_angle_rad=angle.copy(),
                delta_p=post_delta_p.copy(),
                delta_q=post_delta_q.copy(),
                max_mismatch=post_mismatch,
                metadata={
                    "pre_update_max_mismatch": pre_update_mismatch,
                    "active_linear_solve": _compact_linear_metadata(active_result),
                    "reactive_linear_solve": _compact_linear_metadata(reactive_result),
                },
            )
        )

    final_delta_p, final_delta_q, calculated = power_mismatch(case, voltage, angle, ybus)
    final_mismatch = _maximum_mismatch(final_delta_p, final_delta_q)
    converged = final_mismatch < tolerance
    metadata: dict[str, Any] = {
        "b_matrix_mode": b_matrix_mode,
        "formulation": formulation,
        "tolerance": tolerance,
        "fixed_iterations": fixed_iterations,
        "B_prime": b_prime.tolist(),
        "B_double_prime": b_double_prime.tolist(),
        "linear_system_factory": getattr(factory, "name", type(factory).__name__),
    }
    for attribute in ("cache_hits", "cache_misses"):
        if hasattr(factory, attribute):
            metadata[attribute] = int(getattr(factory, attribute))

    return PowerFlowResult(
        solver_name=f"fast_decoupled[{metadata['linear_system_factory']}]",
        converged=converged,
        iterations=len(history),
        voltage_magnitude=voltage,
        voltage_angle_rad=angle,
        specified_power_injection=case.specified_power_injection.copy(),
        calculated_power_injection=calculated,
        max_mismatch=final_mismatch,
        history=history,
        metadata=metadata,
    )


def _newton_jacobian(
    voltage: FloatArray,
    angle: FloatArray,
    ybus: np.ndarray,
    pq: np.ndarray,
    calculated_power: np.ndarray,
) -> FloatArray:
    """Build the polar-coordinate Jacobian for all-PQ non-slack buses."""

    g = ybus.real
    b = ybus.imag
    p = calculated_power.real
    q = calculated_power.imag
    n = len(pq)
    h = np.zeros((n, n), dtype=float)
    n_block = np.zeros((n, n), dtype=float)
    m = np.zeros((n, n), dtype=float)
    l_block = np.zeros((n, n), dtype=float)

    for row, i in enumerate(pq):
        for column, j in enumerate(pq):
            theta_ij = angle[i] - angle[j]
            if i == j:
                h[row, column] = -q[i] - b[i, i] * voltage[i] ** 2
                n_block[row, column] = p[i] / voltage[i] + g[i, i] * voltage[i]
                m[row, column] = p[i] - g[i, i] * voltage[i] ** 2
                l_block[row, column] = q[i] / voltage[i] - b[i, i] * voltage[i]
            else:
                sin_value = np.sin(theta_ij)
                cos_value = np.cos(theta_ij)
                h[row, column] = voltage[i] * voltage[j] * (
                    g[i, j] * sin_value - b[i, j] * cos_value
                )
                n_block[row, column] = voltage[i] * (
                    g[i, j] * cos_value + b[i, j] * sin_value
                )
                m[row, column] = -voltage[i] * voltage[j] * (
                    g[i, j] * cos_value + b[i, j] * sin_value
                )
                l_block[row, column] = voltage[i] * (
                    g[i, j] * sin_value - b[i, j] * cos_value
                )

    return np.block([[h, n_block], [m, l_block]])


def solve_newton_raphson(
    case: PowerFlowCase,
    *,
    tolerance: float = 1e-10,
    max_iterations: int = 30,
    fixed_iterations: int | None = None,
) -> PowerFlowResult:
    """Solve the all-PQ AC equations with a conventional polar Newton method."""

    if tolerance <= 0:
        raise ValueError("tolerance must be positive.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least 1.")

    ybus = case_ybus(case)
    pq = case.pq_buses
    voltage = case.initial_voltage_magnitude.astype(float, copy=True)
    angle = case.initial_voltage_angle_rad.astype(float, copy=True)
    history: list[IterationRecord] = []
    limit = fixed_iterations if fixed_iterations is not None else max_iterations

    for iteration in range(1, limit + 1):
        calculated = calculate_power_injection(voltage, angle, ybus)
        mismatch = case.specified_power_injection[pq] - calculated[pq]
        delta_p = mismatch.real
        delta_q = mismatch.imag
        pre_mismatch = _maximum_mismatch(delta_p, delta_q)
        if fixed_iterations is None and pre_mismatch < tolerance:
            break

        jacobian = _newton_jacobian(voltage, angle, ybus, pq, calculated)
        correction = np.linalg.solve(jacobian, np.concatenate((delta_p, delta_q)))
        angle[pq] += correction[: len(pq)]
        voltage[pq] += correction[len(pq) :]
        if np.any(voltage[pq] <= 0):
            raise RuntimeError("Newton iteration produced a non-positive voltage magnitude.")

        post_delta_p, post_delta_q, _ = power_mismatch(case, voltage, angle, ybus)
        post_mismatch = _maximum_mismatch(post_delta_p, post_delta_q)
        history.append(
            IterationRecord(
                iteration=iteration,
                voltage_magnitude=voltage.copy(),
                voltage_angle_rad=angle.copy(),
                delta_p=post_delta_p.copy(),
                delta_q=post_delta_q.copy(),
                max_mismatch=post_mismatch,
                metadata={
                    "pre_update_max_mismatch": pre_mismatch,
                    "jacobian_condition_number": float(np.linalg.cond(jacobian)),
                },
            )
        )

    final_delta_p, final_delta_q, calculated = power_mismatch(case, voltage, angle, ybus)
    final_mismatch = _maximum_mismatch(final_delta_p, final_delta_q)
    return PowerFlowResult(
        solver_name="newton_raphson",
        converged=final_mismatch < tolerance,
        iterations=len(history),
        voltage_magnitude=voltage,
        voltage_angle_rad=angle,
        specified_power_injection=case.specified_power_injection.copy(),
        calculated_power_injection=calculated,
        max_mismatch=final_mismatch,
        history=history,
        metadata={"tolerance": tolerance, "fixed_iterations": fixed_iterations},
    )
