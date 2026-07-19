# Quantum Power Flow: a reproducible HHL-based implementation

[![CI](https://github.com/TravisCao/quantum-power-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/TravisCao/quantum-power-flow/actions/workflows/ci.yml)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](https://www.python.org/)
[![Qiskit 2.5](https://img.shields.io/badge/Qiskit-2.5.0-6929C4.svg)](https://www.ibm.com/quantum/qiskit)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Reproducibility](https://img.shields.io/badge/reproducibility-documented-brightgreen.svg)](docs/reconstruction_notes.md)

A transparent, end-to-end reproduction of the five-bus **Quantum Power Flow (QPF)** study by Feng, Zhou, and Zhang, implemented with modern Qiskit and Qiskit Aer.

> F. Feng, Y. Zhou, and P. Zhang, “Quantum Power Flow,” arXiv:2104.04888, 2021.

The repository reconstructs the paper’s fast-decoupled AC power-flow model, implements a custom Harrow–Hassidim–Lloyd (HHL) circuit, reproduces the normal and stressed operating cases, evaluates finite phase-register precision, and repeats the 5,000-sample correlated stochastic power-flow experiment.

The emphasis is **reproducibility rather than quantum-speedup claims**: all omitted assumptions, inferred parameters, numerical discrepancies, and simulator-specific choices are documented explicitly.

## Highlights

- Modern-Qiskit implementation of the paper’s enhanced HHL workflow:
  amplitude encoding, quantum phase estimation, reciprocal rotation, inverse QPE, ancilla postselection, and classical scale recovery.
- Classical fast-decoupled and Newton–Raphson baselines implemented from the same AC network model.
- Reuse of matrix-dependent QPE and reciprocal-rotation parameters across power-flow iterations, following the paper’s fixed-Jacobian construction.
- Exact regression tests for network equations, HHL state recovery, deterministic power flow, reconstruction assumptions, and stochastic analysis.
- Reproducible CSV tables, publication-style figures, circuit diagnostics, YAML configurations, and a single-command experiment runner.
- Explicit separation between what is directly specified in the paper and what must be reconstructed from its tables and figures.

## Reproduction summary

| Experiment | Reproduced result | Paper reference / interpretation |
|---|---:|---|
| Test I final voltage at bus 3 | `0.99485952` p.u. | Matches the printed value `0.9948` |
| Test I final voltage at bus 4 | `1.01824660` p.u. | Matches the printed value `1.0182` |
| Test I final angle at bus 3 | `-0.11437525` rad | Matches the printed value `-0.1144` |
| Test I final angle at bus 4 | `-0.03924776` rad | Matches the printed value `-0.0393` |
| Maximum HHL linear-solve error | `2.069e-14` | Statevector simulation, four phase qubits |
| QPF–classical FDLF trajectory difference | `1.513e-15` | Numerically identical within floating-point precision |
| Test II convergence | 32 updates | Paper reports 34; endpoints agree with the plotted curves |
| Stochastic samples converged | `5000 / 5000` | Correlated Gaussian injections, correlation target `0.75` |
| Logical qubits in representative HHL circuit | 7 | 4 phase + 2 system + 1 ancilla |

The detailed machine-readable metrics are stored in [`results/diagnostics/reproduction_metrics.json`](results/diagnostics/reproduction_metrics.json).

## Generated outputs

The reproduction command writes publication-style convergence plots, a phase-register ablation, stochastic-voltage distributions, iteration tables, circuit diagnostics, and machine-readable metrics under `results/`. Full-resolution figures and the 5,000-row Monte Carlo sample table are deterministic generated artifacts and are intentionally not committed; they are recreated by the command below.

## Method overview

For each power-flow iteration, the fast-decoupled equations are written as two constant-matrix linear systems,

$$
B'\,(V\,\Delta\theta)=\Delta P/V,
\qquad
B''\,\Delta V=\Delta Q/V.
$$

The reduced matrices are real, symmetric, sparse, and iteration-independent for the reconstructed five-bus case. The HHL solver therefore separates the computation into:

1. **Right-hand-side state preparation** — normalize and amplitude-encode the active- or reactive-power mismatch.
2. **Quantum phase estimation** — encode the eigenvalues of the fixed reduced matrix in a four-qubit phase register.
3. **Controlled reciprocal rotation** — map each resolved eigenvalue to an ancilla amplitude proportional to its reciprocal.
4. **Inverse QPE and postselection** — uncompute the phase register and extract the solution state conditioned on the ancilla.
5. **Classical scale recovery** — restore the norm and sign needed for the physical voltage update.
6. **AC mismatch update** — recompute nonlinear power mismatches and continue until convergence.

A detailed equation-to-code map is provided in [`docs/algorithm_mapping.md`](docs/algorithm_mapping.md).

## Repository structure

```text
quantum-power-flow/
├── configs/                  # Normal and stressed five-bus cases
├── docs/                     # Algorithm mapping, reconstruction, limitations
├── notebooks/                # Guided paper-reproduction notebook
├── paper/                    # Citation and links to the original article
├── results/
│   ├── diagnostics/          # Circuit statistics and machine-readable metrics
│   ├── figures/              # Reproduced plots
│   └── tables/               # Iteration traces and Monte Carlo samples
├── scripts/                  # Reproduction and parameter-inference entry points
├── src/qpf_repro/
│   ├── quantum/hhl.py        # Custom modern-Qiskit HHL implementation
│   ├── powerflow.py          # Fast-decoupled and Newton–Raphson solvers
│   ├── network.py            # Y-bus, injections, line flows, B′/B″ matrices
│   ├── stochastic.py         # Correlated stochastic power flow
│   └── experiments/          # End-to-end paper experiment runner
└── tests/                    # Physics, circuit, and regression tests
```

## Installation

Python 3.10–3.13 is supported. The archived reproduction used Python 3.13.5, Qiskit 2.5.0, and Qiskit Aer 0.17.2.

```bash
git clone https://github.com/TravisCao/quantum-power-flow.git
cd quantum-power-flow

python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

## Reproduce the paper

Run every deterministic, stressed, precision-ablation, and stochastic experiment:

```bash
qpf-reproduce all --output results
```

Equivalent script entry point:

```bash
python scripts/reproduce_all.py
```

Repeat the omitted-line-parameter inference independently:

```bash
python scripts/infer_missing_line_data.py
```

Run the verification suite:

```bash
ruff check src tests scripts
pytest -q
```

The complete experiment regenerates the contents of `results/`, including the 5,000-sample stochastic dataset. The large raw Monte Carlo CSV and full-resolution PNG figures are generated on demand rather than stored in the repository; compact diagnostics and validation tables are versioned.

## Configuration

The primary assumptions are exposed in [`configs/paper_case5.yaml`](configs/paper_case5.yaml), including:

- five-bus topology and bus injections;
- slack-bus voltage;
- reconstructed common branch impedance;
- convergence tolerance;
- four-qubit phase register and phase scale;
- stochastic sample count, seed, target correlation, and marginal standard deviation.

The stressed operating case is defined separately in [`configs/stressed_case5.yaml`](configs/stressed_case5.yaml).

## Reproducibility qualifications

The source paper is a short proof-of-concept letter and does not publish every numerical input required for a literal rerun. This repository therefore distinguishes **direct reproduction** from **documented reconstruction**.

1. **Line impedances are not reported.** The six branches are reconstructed as `z = 0.02 + j0.20` p.u. by fitting the terminal state in Table I. The least-squares estimate from rounded values is `0.02007846 + j0.19995804` p.u.
2. **Gaussian marginal variances are not reported.** The stochastic experiment uses a documented 1% relative standard deviation, selected to match the displayed ranges in the paper’s stochastic figure.
3. **One intermediate Table-I angle appears inconsistent.** The printed second-iteration `theta4 = -0.0340` is discontinuous with adjacent iterations and cannot be reproduced by a physically consistent network that retains the reported terminal solution.
4. **The stressed case converges in 32 rather than 34 updates.** This difference is consistent with sensitivity to unpublished line-data precision, stopping norm, or internal rounding near the solvability boundary.
5. **The original Qiskit 0.23.4 environment is obsolete.** The implementation is a source-level port to current Qiskit APIs, not an installation of the legacy stack.

Full derivations and numerical evidence are in [`docs/reconstruction_notes.md`](docs/reconstruction_notes.md).

## Interpretation and non-claims

This repository reproduces the paper’s **algorithmic proof of concept** on Qiskit Aer statevectors. It does not establish an end-to-end quantum advantage.

- Dense amplitude-state preparation is not free for a general right-hand side.
- Reading every component of an amplitude-encoded solution requires additional measurement or tomography.
- The 4-by-4 matrix exponential is compiled exactly as a dense unitary; this is not a scalable sparse-Hamiltonian oracle.
- A representative seven-qubit circuit transpiles to depth 817 with 437 `CX` gates in the pinned simulator environment.
- Classical direct solvers are overwhelmingly faster for this small network.

The scientifically useful result is a transparent account of the quantum states, phase encoding, reciprocal rotation, postselection, scaling, and classical coupling needed to make HHL-based fast-decoupled power flow numerically reproduce the reported case study. See [`docs/limitations_and_interpretation.md`](docs/limitations_and_interpretation.md).

## Notebook

[`notebooks/reproduce_paper.ipynb`](notebooks/reproduce_paper.ipynb) provides a guided route through:

- loading the five-bus case;
- constructing the network matrices;
- comparing direct and HHL linear solves;
- reproducing Test I and Test II;
- running the phase-register ablation;
- inspecting the stochastic results.

## Citation

When using this repository, please cite the original paper and the software implementation. Machine-readable citation metadata are included in [`CITATION.cff`](CITATION.cff).

```bibtex
@article{feng2021quantum,
  title   = {Quantum Power Flow},
  author  = {Feng, Fei and Zhou, Yifan and Zhang, Peng},
  journal = {arXiv preprint arXiv:2104.04888},
  year    = {2021}
}
```

## Contributing

Reproduction corrections, numerical cross-checks, and alternative quantum linear-system backends are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.

## License

The implementation is released under the [MIT License](LICENSE). The original paper remains subject to its authors’ and publisher’s terms; its PDF is linked rather than redistributed.
