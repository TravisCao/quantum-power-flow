"""Core data models shared by the power-flow implementations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]
ComplexArray = NDArray[np.complex128]


@dataclass(frozen=True, slots=True)
class Branch:
    """A symmetric pi-model transmission branch in per-unit values."""

    from_bus: int
    to_bus: int
    r_pu: float
    x_pu: float
    b_shunt_pu: float = 0.0

    def __post_init__(self) -> None:
        if self.from_bus == self.to_bus:
            raise ValueError("A branch must connect two distinct buses.")
        if self.r_pu == 0.0 and self.x_pu == 0.0:
            raise ValueError("A branch impedance cannot be zero.")

    @property
    def series_admittance(self) -> complex:
        return 1.0 / complex(self.r_pu, self.x_pu)


@dataclass(frozen=True, slots=True)
class PowerFlowCase:
    """An all-PQ AC power-flow case with one slack bus."""

    name: str
    base_mva: float
    bus_labels: tuple[int, ...]
    slack_bus: int
    branches: tuple[Branch, ...]
    specified_power_injection: ComplexArray
    initial_voltage_magnitude: FloatArray
    initial_voltage_angle_rad: FloatArray

    def __post_init__(self) -> None:
        n_buses = len(self.bus_labels)
        if not 0 <= self.slack_bus < n_buses:
            raise ValueError("slack_bus is outside the bus range.")
        for name, values in (
            ("specified_power_injection", self.specified_power_injection),
            ("initial_voltage_magnitude", self.initial_voltage_magnitude),
            ("initial_voltage_angle_rad", self.initial_voltage_angle_rad),
        ):
            if np.asarray(values).shape != (n_buses,):
                raise ValueError(f"{name} must have shape ({n_buses},).")
        for branch in self.branches:
            if not 0 <= branch.from_bus < n_buses or not 0 <= branch.to_bus < n_buses:
                raise ValueError("A branch endpoint is outside the bus range.")

    @property
    def n_buses(self) -> int:
        return len(self.bus_labels)

    @property
    def pq_buses(self) -> NDArray[np.int64]:
        return np.asarray([index for index in range(self.n_buses) if index != self.slack_bus])


@dataclass(slots=True)
class IterationRecord:
    iteration: int
    voltage_magnitude: FloatArray
    voltage_angle_rad: FloatArray
    delta_p: FloatArray
    delta_q: FloatArray
    max_mismatch: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PowerFlowResult:
    solver_name: str
    converged: bool
    iterations: int
    voltage_magnitude: FloatArray
    voltage_angle_rad: FloatArray
    specified_power_injection: ComplexArray
    calculated_power_injection: ComplexArray
    max_mismatch: float
    history: list[IterationRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
