# Changelog

All notable changes to this reproduction are documented here.

## Unreleased

### Added

- README results section with committed reproduction figures, a Mermaid algorithm
  diagram, and reader-oriented figure labels; `results/figures/` is now versioned and
  regenerated deterministically by the reproduction command.
- Guided student notebook with an iterative algorithm diagram, linear equations, beginner pseudocode, convergence logs, demand and quantum-precision controls, stochastic voltage distributions, result comparisons, and an explained Qiskit circuit.
- Optional notebook environment with JupyterLab and circuit-drawing support.

## 0.1.0 — 2026-07-19

### Added

- Modern-Qiskit implementation of HHL for the fixed fast-decoupled power-flow matrices.
- Five-bus AC network reconstruction and parameter-inference script.
- Classical fast-decoupled and Newton–Raphson baselines.
- Normal, stressed, phase-register, and 5,000-sample stochastic experiments.
- Reproduced tables, figures, circuit diagnostics, and machine-readable metrics.
- Automated regression tests and GitHub Actions CI.
- Documentation of reconstruction assumptions, discrepancies, and quantum-complexity limitations.
