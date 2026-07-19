from __future__ import annotations

import numpy as np

from qpf_repro.cases import paper_case5, stressed_paper_case5
from qpf_repro.powerflow import solve_fast_decoupled
from qpf_repro.quantum import QiskitHHLFactory
from qpf_repro.reference_data import PAPER_TABLE_I_QPF


def _paper_state_trace(result: object) -> np.ndarray:
    return np.asarray(
        [
            [
                record.voltage_magnitude[2],
                record.voltage_magnitude[3],
                record.voltage_angle_rad[2],
                record.voltage_angle_rad[3],
            ]
            for record in result.history
        ]
    )


def test_test_i_quantum_and_classical_trajectories_are_identical() -> None:
    case = paper_case5()
    classical = solve_fast_decoupled(case, fixed_iterations=6)
    quantum = solve_fast_decoupled(
        case,
        linear_system_factory=QiskitHHLFactory(),
        fixed_iterations=6,
    )
    assert np.max(np.abs(_paper_state_trace(classical) - _paper_state_trace(quantum))) < 1e-11


def test_test_i_trace_matches_table_except_suspected_iteration_two_typo() -> None:
    result = solve_fast_decoupled(paper_case5(), fixed_iterations=6)
    reproduced = _paper_state_trace(result)
    published = PAPER_TABLE_I_QPF[:, 1:]
    errors = np.abs(reproduced - published)
    errors[1, 3] = 0.0  # Printed theta4=-0.0340 is inconsistent with adjacent iterations.
    assert np.max(errors) < 1.1e-4
    assert abs(reproduced[1, 3] - published[1, 3]) > 5e-3


def test_stressed_case_converges_to_figure_endpoints() -> None:
    result = solve_fast_decoupled(stressed_paper_case5(), tolerance=1e-5, max_iterations=100)
    assert result.converged
    assert 30 <= result.iterations <= 34
    assert abs(result.voltage_magnitude[0] - 0.674) < 2e-3
    assert abs(result.voltage_magnitude[1] - 0.781) < 2e-3
