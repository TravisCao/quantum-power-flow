#!/usr/bin/env python3
"""Infer the common branch impedance omitted from the paper."""

from qpf_repro.inference import infer_common_bottom_triangle_impedance

if __name__ == "__main__":
    result = infer_common_bottom_triangle_impedance()
    print("Least-squares admittance:", result.admittance)
    print("Inferred branch impedance:", result.impedance)
    print("Power-equation residual norm:", result.residual_norm)
