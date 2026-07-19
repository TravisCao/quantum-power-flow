from __future__ import annotations

import numpy as np
from qpf_repro.cases import paper_case5
from qpf_repro.inference import infer_common_bottom_triangle_impedance

from qpf_repro.network import fast_decoupled_matrices
from qpf_repro.powerflow import solve_newton_raphson


def test_missing_line_impedance_is_recovered_from_published_terminal_state() -> None:
    inferred = infer_common_bottom_triangle_impedance()
    assert abs(inferred.impedance.real - 0.02) < 1.0e-4
    assert abs(inferred.impedance.imag - 0.20) < 1.0e-4
    assert inferred.residual_norm < 5.0e-4


def test_reduced_fast_decoupled_matrices_are_symmetric_positive_definite() -> None:
    b_prime, b_double_prime = fast_decoupled_matrices(paper_case5())
    assert np.allclose(b_prime, b_prime.T)
    assert np.allclose(b_double_prime, b_double_prime.T)
    assert np.min(np.linalg.eigvalsh(b_prime)) > 0
    assert np.allclose(
        np.linalg.eigvalsh(b_prime),
        [4.95049505, 4.95049505, 14.85148515, 14.85148515],
    )


def test_newton_final_state_matches_published_terminal_solution() -> None:
    result = solve_newton_raphson(paper_case5(), tolerance=1e-12)
    assert result.converged
    assert abs(result.voltage_magnitude[2] - 0.9948) < 1.0e-4
    assert abs(result.voltage_magnitude[3] - 1.0182) < 1.0e-4
    assert abs(result.voltage_angle_rad[2] - (-0.1144)) < 1.0e-4
    assert abs(result.voltage_angle_rad[3] - (-0.0392)) < 1.0e-4
