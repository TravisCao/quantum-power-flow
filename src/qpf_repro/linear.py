"""Interfaces and classical baseline for reusable linear systems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np

from .models import FloatArray


@dataclass(slots=True)
class LinearSolveResult:
    solution: FloatArray
    residual_norm: float
    metadata: dict[str, Any] = field(default_factory=dict)


class PreparedLinearSystem(Protocol):
    def solve(self, rhs: FloatArray) -> LinearSolveResult: ...

    def solve_many(self, right_hand_sides: FloatArray) -> FloatArray: ...


class LinearSystemFactory(Protocol):
    name: str

    def prepare(self, matrix: FloatArray, *, label: str = "A") -> PreparedLinearSystem: ...


@dataclass(frozen=True, slots=True)
class NumpyPreparedLinearSystem:
    matrix: FloatArray
    label: str

    def solve(self, rhs: FloatArray) -> LinearSolveResult:
        right_hand_side = np.asarray(rhs, dtype=float)
        solution = np.linalg.solve(self.matrix, right_hand_side)
        return LinearSolveResult(
            solution=np.asarray(solution, dtype=float),
            residual_norm=float(np.linalg.norm(self.matrix @ solution - right_hand_side)),
            metadata={"backend": "numpy_linalg_solve"},
        )

    def solve_many(self, right_hand_sides: FloatArray) -> FloatArray:
        right_hand_sides = np.asarray(right_hand_sides, dtype=float)
        return np.linalg.solve(self.matrix, right_hand_sides.T).T


@dataclass(slots=True)
class NumpyLinearSystemFactory:
    name: str = "numpy"

    def prepare(self, matrix: FloatArray, *, label: str = "A") -> NumpyPreparedLinearSystem:
        array = np.asarray(matrix, dtype=float)
        return NumpyPreparedLinearSystem(array, label)
