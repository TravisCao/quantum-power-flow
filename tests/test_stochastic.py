from __future__ import annotations

import numpy as np

from qpf_repro.cases import paper_case5
from qpf_repro.network import fast_decoupled_matrices
from qpf_repro.quantum import QiskitHHLFactory
from qpf_repro.stochastic import run_stochastic_qpf


def test_small_stochastic_batch_converges_and_preserves_requested_correlation() -> None:
    case = paper_case5()
    matrix, _ = fast_decoupled_matrices(case)
    prepared = QiskitHHLFactory().prepare(matrix)
    result = run_stochastic_qpf(
        case,
        active_system=prepared,
        reactive_system=prepared,
        n_samples=300,
        seed=123,
    )
    assert np.all(result.converged)
    assert abs(result.metadata["empirical_injection_correlation"] - 0.75) < 0.1
    assert result.samples["V3_pu"].between(0.99, 1.00).all()
    assert result.samples["V4_pu"].between(1.01, 1.03).all()
