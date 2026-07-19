# Contributing

Contributions that improve correctness, transparency, testing, or reproducibility are welcome.

## Scope

Good contributions include:

- independent checks of the reconstructed five-bus parameters;
- corrections to the AC power-flow or HHL implementation;
- additional regression tests;
- support for another maintained quantum software backend;
- clearer documentation of assumptions or numerical limitations;
- experiments that separate algorithmic behavior from simulator artifacts.

Please avoid presenting simulator results as hardware speedup evidence without a complete accounting of state preparation, Hamiltonian simulation, measurement, and classical post-processing.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Before submitting a pull request, run:

```bash
ruff check src tests scripts
pytest -q
```

For changes that affect numerical outputs, also run:

```bash
qpf-reproduce all --output results
```

## Pull requests

A pull request should state:

1. the numerical or software issue being addressed;
2. the assumptions introduced or changed;
3. the tests used to validate the change;
4. whether existing result files are expected to change;
5. any remaining discrepancy with the source paper.

Keep scientific claims proportional to the evidence. Where the paper omits an input, label the chosen value as a reconstruction rather than an original-paper parameter.
