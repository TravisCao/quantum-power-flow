"""End-to-end reproduction driver."""

from __future__ import annotations

import platform
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from ..cases import paper_case5, stressed_paper_case5
from ..inference import infer_common_bottom_triangle_impedance
from ..network import branch_power_flows, fast_decoupled_matrices
from ..plotting import (
    save_phase_precision_plot,
    save_stochastic_figure,
    save_test_i_trace_plot,
    save_test_ii_voltage_plot,
)
from ..powerflow import solve_fast_decoupled, solve_newton_raphson
from ..quantum import HHLConfiguration, QiskitHHLFactory
from ..reference_data import paper_table_i_dataframe
from ..reporting import history_dataframe, power_flow_summary, write_json
from ..stochastic import run_stochastic_qpf


def reproduce_all(output: str | Path = "results") -> dict[str, object]:
    root = Path(output)
    tables, figures, diagnostics = root / "tables", root / "figures", root / "diagnostics"
    for path in (tables, figures, diagnostics):
        path.mkdir(parents=True, exist_ok=True)

    case = paper_case5()
    classical = solve_fast_decoupled(case, fixed_iterations=6)
    factory = QiskitHHLFactory()
    quantum = solve_fast_decoupled(case, linear_system_factory=factory, fixed_iterations=6)
    newton = solve_newton_raphson(case, fixed_iterations=3)
    paper = paper_table_i_dataframe()
    classical_trace = history_dataframe(classical)
    quantum_trace = history_dataframe(quantum)
    classical_trace.to_csv(tables / "test_i_classical_fdlf_trace.csv", index=False)
    quantum_trace.to_csv(tables / "test_i_qiskit_hhl_trace.csv", index=False)
    pd.DataFrame(
        branch_power_flows(case, quantum.voltage_magnitude, quantum.voltage_angle_rad)
    ).to_csv(tables / "test_i_branch_flows.csv", index=False)
    save_test_i_trace_plot(
        paper, classical_trace, quantum_trace, figures / "test_i_iteration_trace.png"
    )

    stressed = stressed_paper_case5()
    stressed_classical = solve_fast_decoupled(stressed, tolerance=1e-5)
    stressed_quantum = solve_fast_decoupled(stressed, linear_system_factory=factory, tolerance=1e-5)
    history_dataframe(stressed_quantum, buses=(0, 1, 2, 3)).to_csv(
        tables / "test_ii_quantum_trace.csv", index=False
    )
    save_test_ii_voltage_plot(
        stressed_classical, stressed_quantum, figures / "test_ii_voltage_convergence.png"
    )

    matrix, _ = fast_decoupled_matrices(case, mode="reactance_only")
    rhs = np.asarray([-0.55, -0.55, -0.95, 0.20])
    ablation_rows = []
    for n_phase in (2, 3, 4, 5):
        prepared = QiskitHHLFactory(
            HHLConfiguration(phase_qubits=n_phase, scale_strategy="fixed", fixed_scale=16.0)
        ).prepare(matrix)
        result = prepared.solve(rhs)
        ablation_rows.append(
            {
                "phase_qubits": n_phase,
                "relative_solution_error": result.metadata["relative_solution_error_vs_direct"],
                "residual_norm": result.residual_norm,
                "solution_state_fidelity": result.metadata["solution_state_fidelity_vs_direct"],
            }
        )
    ablation = pd.DataFrame(ablation_rows)
    ablation.to_csv(tables / "phase_register_precision_ablation.csv", index=False)
    save_phase_precision_plot(ablation, figures / "phase_register_precision_ablation.png")

    b_prime, b_double_prime = fast_decoupled_matrices(case)
    active = factory.prepare(b_prime, label="B_prime")
    reactive = factory.prepare(b_double_prime, label="B_double_prime")
    stochastic = run_stochastic_qpf(case, active_system=active, reactive_system=reactive)
    stochastic.samples.to_csv(tables / "stochastic_5000_samples.csv", index=False)
    save_stochastic_figure(stochastic.samples, figures / "stochastic_voltage_distributions.png")

    inference = infer_common_bottom_triangle_impedance()
    metrics: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "qiskit": version("qiskit"),
            "qiskit-aer": version("qiskit-aer"),
            "numpy": version("numpy"),
        },
        "test_i": {
            "quantum_final": {
                "V3": float(quantum.voltage_magnitude[2]),
                "V4": float(quantum.voltage_magnitude[3]),
                "theta3_rad": float(quantum.voltage_angle_rad[2]),
                "theta4_rad": float(quantum.voltage_angle_rad[3]),
            },
            "maximum_quantum_classical_state_difference": float(
                max(
                    np.max(np.abs(quantum.voltage_magnitude - classical.voltage_magnitude)),
                    np.max(np.abs(quantum.voltage_angle_rad - classical.voltage_angle_rad)),
                )
            ),
            "classical": power_flow_summary(classical, case.bus_labels),
            "quantum": power_flow_summary(quantum, case.bus_labels),
            "newton": power_flow_summary(newton, case.bus_labels),
        },
        "test_ii": {
            "paper_reported_iterations": 34,
            "quantum_iterations": stressed_quantum.iterations,
            "quantum_final_V1": float(stressed_quantum.voltage_magnitude[0]),
            "quantum_final_V2": float(stressed_quantum.voltage_magnitude[1]),
        },
        "stochastic": stochastic.metadata,
        "line_inference": inference.to_dict(),
        "quantum_circuit": active.circuit_statistics(),
        "phase_precision_ablation": ablation_rows,
    }
    write_json(diagnostics / "reproduction_metrics.json", metrics)
    write_json(diagnostics / "inferred_line_impedance.json", inference.to_dict())
    write_json(diagnostics / "stochastic_summary.json", stochastic.metadata)
    write_json(diagnostics / "hhl_circuit_statistics.json", active.circuit_statistics())
    return metrics
