"""Tabular and JSON serialization helpers for experiment outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .models import PowerFlowResult


def history_dataframe(
    result: PowerFlowResult, *, buses: tuple[int, ...] = (2, 3)
) -> pd.DataFrame:
    rows: list[dict[str, float | int]] = []
    for record in result.history:
        row: dict[str, float | int] = {
            "iteration": record.iteration,
            "max_mismatch": record.max_mismatch,
        }
        for bus in buses:
            label = bus + 1
            row[f"V{label}"] = float(record.voltage_magnitude[bus])
            row[f"theta{label}_rad"] = float(record.voltage_angle_rad[bus])
        rows.append(row)
    return pd.DataFrame(rows)


def power_flow_summary(result: PowerFlowResult, bus_labels: tuple[int, ...]) -> dict[str, Any]:
    buses = []
    for index, label in enumerate(bus_labels):
        specified = result.specified_power_injection[index]
        calculated = result.calculated_power_injection[index]
        buses.append(
            {
                "bus": label,
                "voltage_magnitude_pu": float(result.voltage_magnitude[index]),
                "voltage_angle_rad": float(result.voltage_angle_rad[index]),
                "specified_p_pu": float(specified.real),
                "specified_q_pu": float(specified.imag),
                "calculated_p_pu": float(calculated.real),
                "calculated_q_pu": float(calculated.imag),
            }
        )
    return {
        "solver": result.solver_name,
        "converged": result.converged,
        "iterations": result.iterations,
        "max_mismatch": result.max_mismatch,
        "buses": buses,
        "metadata": result.metadata,
    }


def write_json(path: str | Path, value: object) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
