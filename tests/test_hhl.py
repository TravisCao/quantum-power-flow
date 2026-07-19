from __future__ import annotations

import numpy as np
from qpf_repro.cases import paper_case5

from qpf_repro.network import fast_decoupled_matrices
from qpf_repro.quantum import HHLConfiguration, QiskitHHLFactory


def test_four_phase_qubit_hhl_matches_direct_solve() -> None:
    matrix, _ = fast_decoupled_matrices(paper_case5())
    rhs = np.asarray([-0.55, -0.55, -0.95, 0.20])
    prepared = QiskitHHLFactory().prepare(matrix, label="B_prime")
    result = prepared.solve(rhs)
    direct = np.linalg.solve(matrix, rhs)
    assert np.linalg.norm(result.solution - direct) / np.linalg.norm(direct) < 1e-10
    assert result.residual_norm < 1e-10
    assert result.metadata["solution_state_fidelity_vs_direct"] > 1 - 1e-12
    assert prepared.logical_qubits == 7
    assert prepared.calibration.logical_phase_bins.tolist() == [5, 5, 15, 15]


def test_prepared_hhl_matrix_is_reused() -> None:
    matrix, _ = fast_decoupled_matrices(paper_case5())
    factory = QiskitHHLFactory()
    first = factory.prepare(matrix, label="first")
    second = factory.prepare(matrix.copy(), label="second")
    assert first is second
    assert factory.cache_misses == 1
    assert factory.cache_hits == 1


def test_less_than_four_phase_qubits_degrades_fixed_scale_solution() -> None:
    matrix, _ = fast_decoupled_matrices(paper_case5(), mode="reactance_only")
    rhs = np.asarray([-0.55, -0.55, -0.95, 0.20])
    direct = np.linalg.solve(matrix, rhs)

    errors: dict[int, float] = {}
    for phase_qubits in (3, 4):
        config = HHLConfiguration(
            phase_qubits=phase_qubits,
            scale_strategy="fixed",
            fixed_scale=16.0,
        )
        prepared = QiskitHHLFactory(configuration=config).prepare(matrix)
        solved = prepared.solve(rhs).solution
        errors[phase_qubits] = float(np.linalg.norm(solved - direct) / np.linalg.norm(direct))

    assert errors[4] < 1e-10
    assert errors[3] > 1e-3
