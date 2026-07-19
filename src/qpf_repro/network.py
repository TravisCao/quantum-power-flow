"""AC network calculations and constant fast-decoupled matrices."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from .models import Branch, ComplexArray, FloatArray, PowerFlowCase


def build_ybus(n_buses: int, branches: tuple[Branch, ...]) -> ComplexArray:
    """Build the nodal admittance matrix for symmetric pi-model branches."""

    ybus = np.zeros((n_buses, n_buses), dtype=complex)
    for branch in branches:
        i, j = branch.from_bus, branch.to_bus
        y = branch.series_admittance
        y_shunt_half = 0.5j * branch.b_shunt_pu
        ybus[i, i] += y + y_shunt_half
        ybus[j, j] += y + y_shunt_half
        ybus[i, j] -= y
        ybus[j, i] -= y
    return ybus


def case_ybus(case: PowerFlowCase) -> ComplexArray:
    return build_ybus(case.n_buses, case.branches)


def voltage_phasor(voltage_magnitude: FloatArray, voltage_angle_rad: FloatArray) -> ComplexArray:
    return voltage_magnitude * np.exp(1j * voltage_angle_rad)


def calculate_power_injection(
    voltage_magnitude: FloatArray,
    voltage_angle_rad: FloatArray,
    ybus: ComplexArray,
) -> ComplexArray:
    """Calculate complex nodal injections ``S = V * conj(Y V)``."""

    v = voltage_phasor(voltage_magnitude, voltage_angle_rad)
    return v * np.conjugate(ybus @ v)


def power_mismatch(
    case: PowerFlowCase,
    voltage_magnitude: FloatArray,
    voltage_angle_rad: FloatArray,
    ybus: ComplexArray | None = None,
) -> tuple[FloatArray, FloatArray, ComplexArray]:
    """Return active/reactive mismatches on PQ buses and all calculated injections."""

    matrix = case_ybus(case) if ybus is None else ybus
    calculated = calculate_power_injection(voltage_magnitude, voltage_angle_rad, matrix)
    pq = case.pq_buses
    mismatch = case.specified_power_injection[pq] - calculated[pq]
    return mismatch.real.copy(), mismatch.imag.copy(), calculated


def reactance_only_ybus(case: PowerFlowCase) -> ComplexArray:
    """Build a lossless admittance matrix from branch reactances only."""

    branches = tuple(
        Branch(
            from_bus=branch.from_bus,
            to_bus=branch.to_bus,
            r_pu=0.0,
            x_pu=branch.x_pu,
            b_shunt_pu=0.0,
        )
        for branch in case.branches
    )
    return build_ybus(case.n_buses, branches)


def fast_decoupled_matrices(
    case: PowerFlowCase,
    *,
    mode: str = "full_imaginary_ybus",
) -> tuple[FloatArray, FloatArray]:
    """Construct the constant Hermitian matrices ``B'`` and ``B''``.

    Parameters
    ----------
    mode:
        ``full_imaginary_ybus`` uses ``-Im(Ybus)`` for both matrices. This mode best matches the
        printed Table I under the reconstructed line data. ``reactance_only`` uses a lossless
        ``1/jx`` network. ``standard_mixed`` uses lossless ``B'`` and full ``B''``.
    """

    pq = case.pq_buses
    full = -case_ybus(case).imag[np.ix_(pq, pq)]
    lossless = -reactance_only_ybus(case).imag[np.ix_(pq, pq)]

    if mode == "full_imaginary_ybus":
        b_prime, b_double_prime = full, full.copy()
    elif mode == "reactance_only":
        b_prime, b_double_prime = lossless, lossless.copy()
    elif mode == "standard_mixed":
        b_prime, b_double_prime = lossless, full
    else:
        raise ValueError(
            "Unknown B-matrix mode. Expected 'full_imaginary_ybus', 'reactance_only', "
            "or 'standard_mixed'."
        )

    for name, matrix in (("B'", b_prime), ("B''", b_double_prime)):
        if not np.allclose(matrix, matrix.T, atol=1e-12):
            raise ValueError(f"{name} is not symmetric/Hermitian.")
        if np.min(np.linalg.eigvalsh(matrix)) <= 0:
            raise ValueError(f"{name} is not positive definite after removing the slack bus.")

    return np.asarray(b_prime, dtype=float), np.asarray(b_double_prime, dtype=float)


def branch_power_flows(
    case: PowerFlowCase,
    voltage_magnitude: FloatArray,
    voltage_angle_rad: FloatArray,
) -> list[dict[str, float | int]]:
    """Return directional branch flows for reporting."""

    v = voltage_phasor(voltage_magnitude, voltage_angle_rad)
    rows: list[dict[str, float | int]] = []
    for branch in case.branches:
        i, j = branch.from_bus, branch.to_bus
        y = branch.series_admittance
        y_sh = 0.5j * branch.b_shunt_pu
        i_ij = (v[i] - v[j]) * y + v[i] * y_sh
        i_ji = (v[j] - v[i]) * y + v[j] * y_sh
        s_ij = v[i] * np.conjugate(i_ij)
        s_ji = v[j] * np.conjugate(i_ji)
        rows.append(
            {
                "from_bus": case.bus_labels[i],
                "to_bus": case.bus_labels[j],
                "p_from_to_pu": float(s_ij.real),
                "q_from_to_pu": float(s_ij.imag),
                "p_to_from_pu": float(s_ji.real),
                "q_to_from_pu": float(s_ji.imag),
                "p_loss_pu": float((s_ij + s_ji).real),
                "q_loss_pu": float((s_ij + s_ji).imag),
            }
        )
    return rows


def is_block_diagonal(matrix: NDArray[np.floating], *, tolerance: float = 1e-12) -> bool:
    """Small helper used in diagnostics; not required by the solver."""

    n = matrix.shape[0]
    if n % 2:
        return False
    half = n // 2
    return bool(
        np.all(np.abs(matrix[:half, half:]) <= tolerance)
        and np.all(np.abs(matrix[half:, :half]) <= tolerance)
    )
