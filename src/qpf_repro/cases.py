"""Reconstructed five-bus cases from the source paper."""

from __future__ import annotations

import numpy as np

from .models import Branch, PowerFlowCase


def _branches() -> tuple[Branch, ...]:
    endpoints = ((0, 4), (0, 1), (1, 4), (2, 4), (2, 3), (3, 4))
    return tuple(Branch(start, end, r_pu=0.02, x_pu=0.20) for start, end in endpoints)


def paper_case5() -> PowerFlowCase:
    """Return the reconstructed normal five-bus case."""

    return PowerFlowCase(
        name="paper_case5_reconstructed",
        base_mva=100.0,
        bus_labels=(1, 2, 3, 4, 5),
        slack_bus=4,
        branches=_branches(),
        specified_power_injection=np.asarray(
            [-0.55 - 0.20j, -0.55 - 0.18j, -0.95 - 0.01j, 0.20 + 0.20j, 0.0j],
            dtype=complex,
        ),
        initial_voltage_magnitude=np.asarray([1.0, 1.0, 1.0, 1.0, 1.002]),
        initial_voltage_angle_rad=np.zeros(5, dtype=float),
    )


def stressed_paper_case5() -> PowerFlowCase:
    """Return Test II with the bus-1 load increased to 2.2 + j0.8 p.u."""

    normal = paper_case5()
    injections = normal.specified_power_injection.copy()
    injections[0] = -2.20 - 0.80j
    return PowerFlowCase(
        name="paper_case5_stressed",
        base_mva=normal.base_mva,
        bus_labels=normal.bus_labels,
        slack_bus=normal.slack_bus,
        branches=normal.branches,
        specified_power_injection=injections,
        initial_voltage_magnitude=normal.initial_voltage_magnitude.copy(),
        initial_voltage_angle_rad=normal.initial_voltage_angle_rad.copy(),
    )
