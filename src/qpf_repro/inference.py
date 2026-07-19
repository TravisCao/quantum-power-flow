"""Inference of the common line impedance omitted from the source paper."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _complex_dict(value: complex) -> dict[str, float]:
    return {"real": float(value.real), "imag": float(value.imag)}


@dataclass(frozen=True, slots=True)
class LineImpedanceInference:
    admittance: complex
    impedance: complex
    predicted_s3: complex
    predicted_s4: complex
    residual_norm: float

    def to_dict(self) -> dict[str, object]:
        return {
            "admittance": _complex_dict(self.admittance),
            "impedance": _complex_dict(self.impedance),
            "predicted_s3": _complex_dict(self.predicted_s3),
            "predicted_s4": _complex_dict(self.predicted_s4),
            "residual_norm": self.residual_norm,
        }


def infer_common_bottom_triangle_impedance() -> LineImpedanceInference:
    """Fit one series admittance to the rounded terminal values at buses 3 and 4."""

    voltage = np.asarray(
        [0.9948 * np.exp(-0.1144j), 1.0182 * np.exp(-0.0393j), 1.002 + 0.0j]
    )
    target = np.asarray([-0.95 - 0.01j, 0.20 + 0.20j])
    coefficients = np.asarray(
        [
            voltage[0] * np.conjugate(2.0 * voltage[0] - voltage[1] - voltage[2]),
            voltage[1] * np.conjugate(2.0 * voltage[1] - voltage[0] - voltage[2]),
        ]
    )
    conjugate_admittance = np.vdot(coefficients, target) / np.vdot(
        coefficients, coefficients
    )
    admittance = complex(np.conjugate(conjugate_admittance))
    predicted = coefficients * np.conjugate(admittance)
    return LineImpedanceInference(
        admittance=admittance,
        impedance=1.0 / admittance,
        predicted_s3=complex(predicted[0]),
        predicted_s4=complex(predicted[1]),
        residual_norm=float(np.linalg.norm(predicted - target)),
    )
